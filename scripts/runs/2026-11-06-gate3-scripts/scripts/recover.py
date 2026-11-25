"""ReCoVeR (Sterz et al. 2025, arXiv 2509.14814), unsupervised version, our reimplementation.

refs: paper = 2509.14814 v1 (pdf page). code = hSterz/recover @ 4c6eb4dc (file:line).
"""
import torch

# --- vector collection: paper sec 3.1 eq. 1 (p.4); collect_language_vectors/collect.py ---


def sentence_states(model, input_ids, skip_first=True):
    """per-layer mean hidden state of one sentence, shape (L+1, d) float32.

    rows follow transformers' output_hidden_states (collect.py:105-110): row 0 = embeddings,
    row i = output of layer i-1, last row = after the final norm (output_capturing.py:243 in
    transformers 5.22.1). also returns the last layer's pre-norm mean, shape (d,).
    """
    captured = {}
    last_layer = model.model.layers[-1]
    handle = last_layer.register_forward_hook(lambda m, a, out: captured.update(pre=out))
    try:
        with torch.no_grad():
            out = model(input_ids=input_ids, output_hidden_states=True)
    finally:
        handle.remove()
    states = torch.stack([h[0] for h in out.hidden_states]).float()  # (L+1, s, d)
    pre = captured["pre"][0].float()  # (s, d)
    start = 1 if skip_first else 0  # drop first token: paper footnote 1 (p.4), collect.py:20
    if states.shape[1] <= start:
        return None, None
    return states[:, start:].mean(dim=1).cpu(), pre[start:].mean(dim=0).cpu()


def mean_vectors(per_sentence):
    """language vector = mean over sentences of per-sentence token means (eq. 1, p.4)."""
    return torch.stack(per_sentence).mean(dim=0)


def load_vectors(path, last_layer="postnorm"):
    """{lang: (L+1, d)}. postnorm = their code's last row; prenorm = our labeled variant."""
    from safetensors.torch import load_file
    raw = load_file(path)
    vectors = {k: v for k, v in raw.items() if not k.endswith(".last_prenorm")}
    if last_layer == "prenorm":
        for lang, v in vectors.items():
            v[-1] = raw[f"{lang}.last_prenorm"]
    elif last_layer != "postnorm":
        raise ValueError(last_layer)
    return vectors


# --- steering: paper sec 3.2 eq. 2-3 (p.4-5); recover/steering.py ---


def content_removed(vectors):
    """r_l = v_l - c, c = mean over all collected languages (p.4; steering.py:130-133)."""
    c = torch.stack(list(vectors.values())).mean(dim=0)
    return {lang: v - c for lang, v in vectors.items()}


def steering_dirs(r, target, source=None, beta=1.0):
    """per-layer unit direction, shape (L, d).

    hook on layer i uses row i+1 (steering.py:255-266, offset 1).
    cross: r_tgt - beta*r_src (eq. 3, steering.py:158-162). mono: r_tgt (eq. 2).
    """
    d = r[target][1:].clone()
    if source is not None:
        d = d - beta * r[source][1:]
    norms = torch.linalg.norm(d, dim=-1, keepdim=True)
    if torch.any(norms == 0):
        raise ValueError(f"zero steering vector for {target} vs {source}")
    return d / norms  # scaling_mode "norm" (steering.py:168-172)


class Steerer:
    """adds alpha * dir[i] to the output of decoder layer i, at every position,
    except position 0 on the first (prefill) pass (p.5 top; steering.py:180-181).
    optional per-token norm restore (p.5; steering.py:188-189).
    """

    def __init__(self, model, alpha, restore_norm):
        self.layers = model.model.layers
        self.alpha = alpha
        self.restore_norm = restore_norm
        self.handles = []
        self.calls = []

    def set(self, dirs):
        self.clear()
        self.calls = [0] * len(self.layers)
        for i, layer in enumerate(self.layers):
            vec = (self.alpha * dirs[i]).float()
            self.handles.append(layer.register_forward_hook(self._hook(i, vec)))

    def _hook(self, i, vec):
        def hook(module, args, output):
            # Qwen3_5DecoderLayer returns a tensor, not a tuple (modeling_qwen3_5.py:861-901)
            h = output
            first_pass = self.calls[i] == 0
            self.calls[i] += 1
            hf = h.float()
            out = hf + vec.to(h.device)
            if first_pass:
                out[:, :1] = hf[:, :1]
            if self.restore_norm:
                out = out / torch.linalg.norm(out, dim=-1, keepdim=True) * torch.linalg.norm(hf, dim=-1, keepdim=True)
            return out.to(h.dtype)
        return hook

    def clear(self):
        for handle in self.handles:
            handle.remove()
        self.handles = []
