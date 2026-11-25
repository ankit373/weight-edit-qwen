"""check the MIT exp8 p50c edit diff against our base weights. cpu, small reads only.

usage: diff_check.py <base.safetensors> <edit_dir> <out.json>

reads the safetensors header and only the edited tensors (by byte offset). own code, not theirs.
diff format from their apply_edit.py:26-36 (sparse: flat int32 idx + uint16 bf16 bits).
"""
import hashlib
import json
import os
import struct
import sys
import zipfile

import numpy as np

# their st_numpy.py:8-9 dtype map, used only to check apply_edit.py can read every tensor
THEIR_DT = {"BF16", "F16", "F32", "F64", "I64", "I32", "I16", "I8", "U8", "BOOL"}


def header(path):
    with open(path, "rb") as f:
        n = struct.unpack("<Q", f.read(8))[0]
        return json.loads(f.read(n)), 8 + n


def read_bf16(path, info, off):
    a, b = info["data_offsets"]
    with open(path, "rb") as f:
        f.seek(off + a)
        raw = f.read(b - a)
    return np.frombuffer(raw, dtype="<u2").reshape(info["shape"]).copy()


def bf16_f32(bits):
    return (bits.astype(np.uint32) << 16).view(np.float32)


def sha(a):
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()


def npz_members(path):
    # npy header of each member, read as text; no array loading here
    out = {}
    with zipfile.ZipFile(path) as z:
        for zi in z.infolist():
            with z.open(zi) as f:
                head = f.read(256).decode("latin1")
            out[zi.filename] = {"size": zi.file_size, "npy_header": head.split("\n")[0][10:]}
    return out


def param_counts(head):
    groups = {}
    for name, info in head.items():
        if name == "__metadata__":
            continue
        g = name.split(".")[1] if name.startswith("model.") else name.split(".")[0]
        groups[g] = groups.get(g, 0) + int(np.prod(info["shape"]))
    return groups


def check_tensor(i, t, z, head, off, base_path):
    info = head[t["name"]]
    base = read_bf16(base_path, info, off)
    idx, val = z[f"t{i}_idx"], z[f"t{i}_val"]
    edited = base.copy().reshape(-1)
    edited[idx] = val  # apply_edit.py:34-35, sparse form
    edited = edited.reshape(base.shape)
    mask = base != edited
    cols = np.flatnonzero(mask.any(0))
    d = bf16_f32(edited).astype(np.float64) - bf16_f32(base).astype(np.float64)
    sub = d[:, cols]
    s = np.linalg.svd(sub, compute_uv=False)
    u = np.linalg.svd(sub, full_matrices=False)[0][:, 0]
    base_cols = bf16_f32(base)[:, cols].astype(np.float64)
    coef = u @ sub  # per-column amount of u1 in the delta (sign of u1 is arbitrary)
    return {
        "delta_coef_on_u1": {"min": float(coef.min()), "max": float(coef.max()),
                             "mean": float(coef.mean()), "std": float(coef.std()),
                             "same_sign_all_cols": bool((coef > 0).all() or (coef < 0).all())},
        "base_cols_coef_on_u1_mean": float((u @ base_cols).mean()),
        "edited_over_base_coef_on_u1": [float(x) for x in np.percentile(
            (u @ (base_cols + sub)) / (u @ base_cols), [0, 50, 100])],
        "name": t["name"], "dtype": info["dtype"], "shape": info["shape"],
        "shape_matches_manifest": info["shape"] == t["shape"],
        "base_sha256": sha(base), "base_sha256_matches_manifest": sha(base) == t["base_sha256"],
        "edited_sha256": sha(edited), "edited_sha256_matches_manifest": sha(edited) == t["edited_sha256"],
        "npz_idx_dtype": str(idx.dtype), "npz_val_dtype": str(val.dtype), "n_idx": int(idx.size),
        "idx_min": int(idx.min()), "idx_max": int(idx.max()), "idx_unique": int(np.unique(idx).size),
        "changed_entries": int(mask.sum()), "changed_columns": int(cols.size),
        "changed_rows": int(mask.any(1).sum()), "changed_column_ids": cols.tolist(),
        "nan_or_inf_in_edited": int((~np.isfinite(bf16_f32(edited))).sum()),
        "relative_change_fro": float(np.linalg.norm(d) / np.linalg.norm(bf16_f32(base))),
        "delta_cols_singular_values_top5": [float(x) for x in s[:5]],
        "delta_cols_rank1_energy_share": float(s[0] ** 2 / (s ** 2).sum()),
        "base_cols_proj_on_u1_mean_abs": float(np.abs(u @ base_cols).mean()),
        "edited_cols_proj_on_u1_mean_abs": float(np.abs(u @ (base_cols + sub)).mean()),
    }


def main(base_path, edit_dir, out_path):
    head, off = header(base_path)
    man = json.load(open(os.path.join(edit_dir, "manifest.json")))
    npz_path = os.path.join(edit_dir, "edit.npz")
    members = npz_members(npz_path)
    z = np.load(npz_path, allow_pickle=False)
    tensors = [check_tensor(i, t, z, head, off, base_path) for i, t in enumerate(man["tensors"])]
    counts = param_counts(head)
    total_all = sum(counts.values())
    lm = counts.get("language_model", 0)
    touched = sum(t["changed_columns"] * t["shape"][0] for t in tensors)
    changed = sum(t["changed_entries"] for t in tensors)
    res = {
        "base_file": base_path, "base_header_tensors": len(head) - ("__metadata__" in head),
        "base_dtypes": sorted({v["dtype"] for k, v in head.items() if k != "__metadata__"}),
        "all_dtypes_readable_by_their_st_numpy": all(
            v["dtype"] in THEIR_DT for k, v in head.items() if k != "__metadata__"),
        "npz_members": members, "manifest_forms": [t["form"] for t in man["tensors"]],
        "tensors": tensors, "param_counts_by_group": counts, "params_total_file": total_all,
        "touched_weights": touched, "changed_entries_total": changed,
        "pct_touched_of_language_model": 100 * touched / lm,
        "pct_changed_of_language_model": 100 * changed / lm,
        "pct_touched_of_whole_file": 100 * touched / total_all,
        "pct_changed_of_whole_file": 100 * changed / total_all,
    }
    json.dump(res, open(out_path, "w"), indent=1)
    short = {k: v for k, v in res.items() if k != "tensors"}
    short["tensors"] = [{k: v for k, v in t.items() if k != "changed_column_ids"} for t in tensors]
    print(json.dumps(short, indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:4])
