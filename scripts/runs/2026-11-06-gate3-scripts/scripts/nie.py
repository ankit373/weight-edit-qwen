"""Nie, Schmid, Schütze 2025 (arXiv 2505.16538): neuron importance at confusion points,
"score" selection (no reference model), and the down_proj column edit. our reimplementation.

refs: paper = 2505.16538 v2 (pdf page). code = ercong21/lang_confusion @ b6e13f60 (file:line).
qwen code = transformers 5.22.1 models/qwen3_5/modeling_qwen3_5.py.
"""
from collections import defaultdict

import torch

import g3common


def capture_last_position(model, input_ids):
    """one forward pass. returns per-layer residual after the token mixer and the FFN
    coefficients at the last position, the final pre-norm hidden state there, and the
    model's top-1 next token (find_neurons.py:162-172).

    residual = input of post_attention_layernorm = h^{l-1} + A^l (paper eq. 2, p.5;
    modeling_qwen3_5.py:892-893). coefficients = input of down_proj = m^l (eq. 3-4, p.5;
    modeling_qwen3_5.py:822-823). final = input of the final norm (find_neurons.py:169).
    """
    layers = model.model.layers
    resid, coef, final = [None] * len(layers), [None] * len(layers), {}
    handles = []
    for i, layer in enumerate(layers):
        handles.append(layer.post_attention_layernorm.register_forward_pre_hook(
            lambda m, a, i=i: resid.__setitem__(i, a[0][0, -1].float())))
        handles.append(layer.mlp.down_proj.register_forward_pre_hook(
            lambda m, a, i=i: coef.__setitem__(i, a[0][0, -1].float())))
    handles.append(model.model.norm.register_forward_pre_hook(
        lambda m, a: final.update(h=a[0][0, -1].float())))
    try:
        with torch.no_grad():
            logits = model(input_ids=input_ids).logits
    finally:
        for h in handles:
            h.remove()
    return resid, coef, final["h"], int(logits[0, -1].argmax())


def unembedding(model):
    """float32 copy of lm_head, made once (tied to embed_tokens: config tie_word_embeddings)."""
    return model.lm_head.weight.detach().float()


def log_prob_fn(model, emb, final_h, target):
    """log p(target | x) with the final norm's variance frozen at the real final state
    (get_bsvalues, find_neurons.py:64-69). qwen norm is x_norm * (1 + w) in float32
    (modeling_qwen3_5.py:833-841), not x_norm * w as in llama.
    """
    norm = model.model.norm
    scale = torch.rsqrt(final_h.pow(2).mean(-1, keepdim=True) + norm.eps)
    gain = 1.0 + norm.weight.float()

    def log_prob(x):
        z = (x * scale * gain) @ emb.T
        return z[..., target] - torch.logsumexp(z, dim=-1)
    return log_prob


@torch.no_grad()
def layer_scores(log_prob, resid, coef, down_w, chunk=512):
    """Imp(v) = log p(w | v + A + h) - log p(w | A + h) for every neuron of one layer
    (paper eq. 5, p.6; find_neurons.py:176-191). v_k = m_k * down[:, k] (eq. 3)."""
    base = log_prob(resid)
    sub = (down_w.float() * coef).T  # (N, d), find_neurons.py:179
    out = torch.empty(sub.shape[0], device=sub.device)
    for s in range(0, sub.shape[0], chunk):
        out[s:s + chunk] = log_prob(resid + sub[s:s + chunk]) - base
    return out


@torch.no_grad()
def prompt_top_neurons(model, emb, input_ids, top_k=300, chunk=512):
    """top_k (layer, neuron, score) for one CP prompt (find_neurons.py:194-205)."""
    resid, coef, final_h, target = capture_last_position(model, input_ids)
    log_prob = log_prob_fn(model, emb, final_h, target)
    per_layer = [layer_scores(log_prob, resid[i], coef[i], layer.mlp.down_proj.weight, chunk)
                 for i, layer in enumerate(model.model.layers)]
    flat = torch.stack(per_layer)  # (L, N)
    vals, idx = torch.topk(flat.flatten(), top_k)
    n = flat.shape[1]
    return target, [(int(j) // n, int(j) % n, float(v)) for v, j in zip(vals.cpu(), idx.cpu())]


def aggregate(per_prompt):
    """sum of scores and count over prompts (find_neurons.py:207-212)."""
    score, freq = defaultdict(float), defaultdict(int)
    for tops in per_prompt:
        for layer, neuron, s in tops:
            score[(layer, neuron)] += s
            freq[(layer, neuron)] += 1
    ranked = sorted(score.items(), key=lambda kv: kv[1], reverse=True)
    return [{"layer": l, "neuron": k, "score": s, "freq": freq[(l, k)]} for (l, k), s in ranked]


def select_score(ranked, n=100):
    """"score" strategy: top n by summed score (paper sec 5.1, p.7; neuron_editing.py:173-176)."""
    return [(r["layer"], r["neuron"]) for r in ranked[:n]]


def zero_columns(model, neurons):
    """set down_proj[:, k] = 0 in layer l (neuron_editing.py:193-197). down_proj has no bias
    (modeling_qwen3_5.py:819), so this equals zeroing the activation (paper C.4, p.15).
    returns the saved columns and a diff record with sha256 of base and edited tensors.
    """
    by_layer = defaultdict(list)
    for layer, k in neurons:
        by_layer[layer].append(k)
    saved, record = {}, []
    for layer, cols in sorted(by_layer.items()):
        w = model.model.layers[layer].mlp.down_proj.weight
        base_sha = g3common.tensor_sha256(w)
        with torch.no_grad():
            saved[layer] = (cols, w[:, cols].clone())
            w[:, cols] = 0
        record.append({"layer": layer, "columns": sorted(cols), "base_sha256": base_sha,
                       "edited_sha256": g3common.tensor_sha256(w)})
    return saved, record


def restore_columns(model, saved):
    with torch.no_grad():
        for layer, (cols, values) in saved.items():
            model.model.layers[layer].mlp.down_proj.weight[:, cols] = values
