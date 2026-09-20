import torch


def ensure_finite_tensor(name, tensor, *, epoch, batch):
    finite_mask = torch.isfinite(tensor)
    if bool(finite_mask.all()):
        return tensor

    finite_values = tensor.detach()[finite_mask]
    finite_min = (
        finite_values.min().cpu().item() if finite_values.numel() else "unavailable"
    )
    finite_max = (
        finite_values.max().cpu().item() if finite_values.numel() else "unavailable"
    )
    non_finite = tensor.numel() - int(finite_mask.sum().cpu().item())
    raise FloatingPointError(
        f"non-finite tensor {name}: epoch={epoch}, batch={batch}, "
        f"non_finite={non_finite}/{tensor.numel()}, "
        f"finite_min={finite_min}, finite_max={finite_max}"
    )


def non_finite_parameter_names(model, *, inspect_gradients):
    names = []
    for name, parameter in model.named_parameters():
        tensor = parameter.grad if inspect_gradients else parameter
        if tensor is not None and not bool(torch.isfinite(tensor).all()):
            names.append(name)
    return names
