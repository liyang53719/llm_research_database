from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'model'))

from accum_v3_model import (  # noqa: E402
    AccumStyle,
    Block64CheckpointCycleModel,
    FP32RecurrentCycleModel,
    FullBF16CycleModel,
    accumulate,
    accumulate_bf16_block_fp32_checkpoint,
    accumulate_bf16_tree_fp32_recurrent,
    accumulate_full_bf16,
    bf16_add,
    bf16_to_float,
    bf16_tree4,
    float_to_bf16,
    product_bits_from_quantized_inputs,
    quantize_bf16_array,
)


class AccumV3Tests(unittest.TestCase):
    def test_bf16_tree_order(self) -> None:
        values = [float_to_bf16(x) for x in (1.0, 2.0, 4.0, 8.0)]
        expected = bf16_add(
            bf16_add(values[0], values[1]),
            bf16_add(values[2], values[3]),
        )
        self.assertEqual(bf16_tree4(values), expected)

    def test_fp32_widen_is_exact(self) -> None:
        for value in (-128.0, -3.25, -0.0, 0.0, 0.125, 1.0, 127.5, 1024.0):
            raw = float_to_bf16(value)
            widened = np.float32(bf16_to_float(raw))
            self.assertEqual(float(widened), float(bf16_to_float(raw)))

    def test_three_styles_known_sequence(self) -> None:
        products = [float_to_bf16(x) for x in (1.0, -0.5, 2.0, 0.25) * 32]
        a = accumulate_full_bf16(products, items_per_cycle=4)
        b = accumulate_bf16_tree_fp32_recurrent(products, items_per_cycle=4)
        c = accumulate_bf16_block_fp32_checkpoint(
            products, items_per_cycle=4, block_products=64
        )
        self.assertTrue(np.isfinite(a))
        self.assertTrue(np.isfinite(b))
        self.assertTrue(np.isfinite(c))
        self.assertEqual(float(b), 88.0)
        self.assertEqual(float(c), 88.0)

    def test_cycle_models_match_batch_functions(self) -> None:
        rng = np.random.default_rng(23)
        values = rng.normal(0.0, 1.0, 256).astype(np.float32)
        products = list(map(int, quantize_bf16_array(values)))

        full = FullBF16CycleModel(items_per_cycle=4)
        fp32 = FP32RecurrentCycleModel(items_per_cycle=4)
        block = Block64CheckpointCycleModel(items_per_cycle=4)
        for start in range(0, len(products), 4):
            chunk = products[start:start + 4]
            full.issue(chunk)
            fp32.issue(chunk)
            block.issue(chunk)
        block.flush()

        self.assertEqual(
            float(bf16_to_float(full.acc)),
            float(accumulate(AccumStyle.FULL_BF16, products, items_per_cycle=4)),
        )
        self.assertEqual(
            float(fp32.acc),
            float(accumulate(
                AccumStyle.BF16_TREE_FP32_RECURRENT,
                products,
                items_per_cycle=4,
            )),
        )
        self.assertEqual(
            float(block.checkpoint),
            float(accumulate(
                AccumStyle.BF16_BLOCK64_FP32_CHECKPOINT,
                products,
                items_per_cycle=4,
            )),
        )

    def test_block64_flush_tail(self) -> None:
        products = [float_to_bf16(1.0)] * 70
        model = Block64CheckpointCycleModel(items_per_cycle=1)
        pulses = 0
        for product in products:
            pulses += int(model.issue([product]).checkpoint_pulse)
        self.assertEqual(pulses, 1)
        self.assertEqual(model.count, 6)
        flushed = model.flush()
        self.assertTrue(flushed.checkpoint_pulse)
        self.assertEqual(float(model.checkpoint), 70.0)

    def test_product_quantization_contract(self) -> None:
        a = quantize_bf16_array(np.array([1.5, -2.0, 0.25], dtype=np.float32))
        b = quantize_bf16_array(np.array([2.0, 0.5, -4.0], dtype=np.float32))
        products = product_bits_from_quantized_inputs(a, b)
        decoded = [float(bf16_to_float(int(x))) for x in products]
        self.assertEqual(decoded, [3.0, -1.0, -1.0])


if __name__ == '__main__':
    unittest.main()
