import unittest

import torch

from experiments.training_diagnostics import (
    ensure_finite_tensor,
    non_finite_parameter_names,
)


class TrainingDiagnosticsTests(unittest.TestCase):
    def test_finite_tensor_passes_through(self):
        tensor = torch.tensor([1.0, -2.0])

        self.assertIs(ensure_finite_tensor("loss", tensor, epoch=1, batch=2), tensor)

    def test_non_finite_tensor_reports_location_and_counts(self):
        tensor = torch.tensor([1.0, float("nan"), float("inf")])

        with self.assertRaisesRegex(
            FloatingPointError,
            r"loss.*epoch=1.*batch=2.*non_finite=2/3.*finite_min=1.0.*finite_max=1.0",
        ):
            ensure_finite_tensor("loss", tensor, epoch=1, batch=2)

    def test_names_parameters_with_non_finite_gradients_or_values(self):
        model = torch.nn.Sequential(torch.nn.Linear(2, 1), torch.nn.Linear(1, 1))
        parameters = dict(model.named_parameters())
        parameters["0.weight"].grad = torch.full_like(
            parameters["0.weight"], float("nan")
        )
        with torch.no_grad():
            parameters["1.bias"].fill_(float("inf"))

        self.assertEqual(
            non_finite_parameter_names(model, inspect_gradients=True),
            ["0.weight"],
        )
        self.assertEqual(
            non_finite_parameter_names(model, inspect_gradients=False),
            ["1.bias"],
        )


if __name__ == "__main__":
    unittest.main()
