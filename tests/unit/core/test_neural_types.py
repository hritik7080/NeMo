# ! /usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2019 NVIDIA. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# =============================================================================

from unittest import TestCase

import pytest

from nemo.backends.pytorch.tutorials import MSELoss, RealFunctionDataLayer, TaylorNet
from nemo.core.neural_types import (
    AcousticEncodedRepresentation,
    AudioSignal,
    AxisKind,
    AxisKindAbstract,
    AxisType,
    ChannelType,
    ElementType,
    MelSpectrogramType,
    MFCCSpectrogramType,
    NeuralPortNmTensorMismatchError,
    NeuralType,
    NeuralTypeComparisonResult,
    SpectrogramType,
    VoidType,
)


class NeuralTypeSystemTests(TestCase):
    @pytest.mark.unit
    def test_short_vs_long_version(self):
        long_version = NeuralType(
            axes=(AxisType(AxisKind.Batch, None), AxisType(AxisKind.Dimension, None), AxisType(AxisKind.Time, None)),
            elements_type=AcousticEncodedRepresentation(),
        )
        short_version = NeuralType(('B', 'D', 'T'), AcousticEncodedRepresentation())
        self.assertEqual(long_version.compare(short_version), NeuralTypeComparisonResult.SAME)
        self.assertEqual(short_version.compare(long_version), NeuralTypeComparisonResult.SAME)

    @pytest.mark.unit
    def test_parameterized_type_audio_sampling_frequency(self):
        audio16K = NeuralType(axes=('B', 'T'), elements_type=AudioSignal(16000))
        audio8K = NeuralType(axes=('B', 'T'), elements_type=AudioSignal(8000))
        another16K = NeuralType(axes=('B', 'T'), elements_type=AudioSignal(16000))

        self.assertEqual(audio8K.compare(audio16K), NeuralTypeComparisonResult.SAME_TYPE_INCOMPATIBLE_PARAMS)
        self.assertEqual(audio16K.compare(audio8K), NeuralTypeComparisonResult.SAME_TYPE_INCOMPATIBLE_PARAMS)
        self.assertEqual(another16K.compare(audio16K), NeuralTypeComparisonResult.SAME)
        self.assertEqual(audio16K.compare(another16K), NeuralTypeComparisonResult.SAME)

    @pytest.mark.unit
    def test_transpose_same_1(self):
        type1 = NeuralType(axes=('B', 'T', 'C'))
        type2 = NeuralType(axes=('T', 'B', 'C'))
        self.assertEqual(type1.compare(type2), NeuralTypeComparisonResult.TRANSPOSE_SAME)
        self.assertEqual(type2.compare(type1), NeuralTypeComparisonResult.TRANSPOSE_SAME)

    @pytest.mark.unit
    def test_transpose_same_2(self):
        audio16K = NeuralType(axes=('B', 'T'), elements_type=AudioSignal(16000))
        audio16K_t = NeuralType(axes=('T', 'B'), elements_type=AudioSignal(16000))
        self.assertEqual(audio16K.compare(audio16K_t), NeuralTypeComparisonResult.TRANSPOSE_SAME)

    @pytest.mark.unit
    def test_inheritance_spec_augment_example(self):
        input = NeuralType(('B', 'D', 'T'), SpectrogramType())
        out1 = NeuralType(('B', 'D', 'T'), MelSpectrogramType())
        out2 = NeuralType(('B', 'D', 'T'), MFCCSpectrogramType())
        self.assertEqual(out1.compare(out2), NeuralTypeComparisonResult.INCOMPATIBLE)
        self.assertEqual(out2.compare(out1), NeuralTypeComparisonResult.INCOMPATIBLE)
        self.assertEqual(input.compare(out1), NeuralTypeComparisonResult.GREATER)
        self.assertEqual(input.compare(out2), NeuralTypeComparisonResult.GREATER)
        self.assertEqual(out1.compare(input), NeuralTypeComparisonResult.LESS)
        self.assertEqual(out2.compare(input), NeuralTypeComparisonResult.LESS)

    @pytest.mark.unit
    def test_singletone(self):
        loss_output1 = NeuralType(axes=None)
        loss_output2 = NeuralType(axes=None)
        self.assertEqual(loss_output1.compare(loss_output2), NeuralTypeComparisonResult.SAME)
        self.assertEqual(loss_output2.compare(loss_output1), NeuralTypeComparisonResult.SAME)

    @pytest.mark.unit
    def test_list_of_lists(self):
        T1 = NeuralType(
            axes=(
                AxisType(kind=AxisKind.Batch, size=None, is_list=True),
                AxisType(kind=AxisKind.Time, size=None, is_list=True),
                AxisType(kind=AxisKind.Dimension, size=32, is_list=False),
                AxisType(kind=AxisKind.Dimension, size=128, is_list=False),
                AxisType(kind=AxisKind.Dimension, size=256, is_list=False),
            ),
            elements_type=ChannelType(),
        )
        T2 = NeuralType(
            axes=(
                AxisType(kind=AxisKind.Batch, size=None, is_list=False),
                AxisType(kind=AxisKind.Time, size=None, is_list=False),
                AxisType(kind=AxisKind.Dimension, size=32, is_list=False),
                AxisType(kind=AxisKind.Dimension, size=128, is_list=False),
                AxisType(kind=AxisKind.Dimension, size=256, is_list=False),
            ),
            elements_type=ChannelType(),
        )
        # TODO: should this be incompatible instead???
        self.assertEqual(T1.compare(T2), NeuralTypeComparisonResult.TRANSPOSE_SAME)

    @pytest.mark.unit
    def test_void(self):
        btc_spctr = NeuralType(('B', 'T', 'C'), SpectrogramType())
        btc_spct_bad = NeuralType(('B', 'T'), SpectrogramType())
        btc_void = NeuralType(('B', 'T', 'C'), VoidType())
        self.assertEqual(btc_void.compare(btc_spctr), NeuralTypeComparisonResult.SAME)
        self.assertEqual(btc_spctr.compare(btc_void), NeuralTypeComparisonResult.INCOMPATIBLE)
        self.assertEqual(btc_void.compare(btc_spct_bad), NeuralTypeComparisonResult.INCOMPATIBLE)

    @pytest.mark.unit
    def test_big_void(self):
        big_void_1 = NeuralType(elements_type=VoidType())
        big_void_2 = NeuralType()

        btc_spctr = NeuralType(('B', 'T', 'C'), SpectrogramType())
        btc_spct_bad = NeuralType(('B', 'T'), SpectrogramType())
        t1 = NeuralType(
            axes=(
                AxisType(kind=AxisKind.Batch, size=None, is_list=True),
                AxisType(kind=AxisKind.Time, size=None, is_list=True),
                AxisType(kind=AxisKind.Dimension, size=32, is_list=False),
                AxisType(kind=AxisKind.Dimension, size=128, is_list=False),
                AxisType(kind=AxisKind.Dimension, size=256, is_list=False),
            ),
            elements_type=ChannelType(),
        )
        t2 = NeuralType(
            axes=(
                AxisType(kind=AxisKind.Batch, size=None, is_list=False),
                AxisType(kind=AxisKind.Time, size=None, is_list=False),
                AxisType(kind=AxisKind.Dimension, size=32, is_list=False),
                AxisType(kind=AxisKind.Dimension, size=128, is_list=False),
                AxisType(kind=AxisKind.Dimension, size=256, is_list=False),
            ),
            elements_type=ChannelType(),
        )

        self.assertEqual(big_void_1.compare(btc_spctr), NeuralTypeComparisonResult.SAME)
        self.assertEqual(big_void_1.compare(btc_spct_bad), NeuralTypeComparisonResult.SAME)
        self.assertEqual(big_void_1.compare(t1), NeuralTypeComparisonResult.SAME)
        self.assertEqual(big_void_1.compare(t2), NeuralTypeComparisonResult.SAME)

        self.assertEqual(big_void_2.compare(btc_spctr), NeuralTypeComparisonResult.SAME)
        self.assertEqual(big_void_2.compare(btc_spct_bad), NeuralTypeComparisonResult.SAME)
        self.assertEqual(big_void_2.compare(t1), NeuralTypeComparisonResult.SAME)
        self.assertEqual(big_void_2.compare(t2), NeuralTypeComparisonResult.SAME)

    @pytest.mark.unit
    def test_dag(self):
        data_source = RealFunctionDataLayer(n=10000, batch_size=128)
        trainable_module = TaylorNet(dim=4)
        loss = MSELoss()
        x, y = data_source()
        y_pred = trainable_module(x=x)
        _ = loss(predictions=y_pred, target=y)

        def wrong():
            data_source = RealFunctionDataLayer(n=10000, batch_size=128)
            trainable_module = TaylorNet(dim=4)
            loss = MSELoss()
            x, y = data_source()
            loss_tensor = loss(predictions=x, target=x)
            _ = trainable_module(x=loss_tensor)

        self.assertRaises(NeuralPortNmTensorMismatchError, wrong)

    @pytest.mark.unit
    def test_unspecified_dimensions(self):
        t0 = NeuralType(
            (AxisType(AxisKind.Batch, 64), AxisType(AxisKind.Time, 10), AxisType(AxisKind.Dimension, 128)),
            SpectrogramType(),
        )
        t1 = NeuralType(('B', 'T', 'C'), SpectrogramType())
        self.assertEqual(t1.compare(t0), NeuralTypeComparisonResult.SAME)
        self.assertEqual(t0.compare(t1), NeuralTypeComparisonResult.DIM_INCOMPATIBLE)

    @pytest.mark.unit
    def test_any_axis(self):
        t0 = NeuralType(('B', 'Any', 'Any'), VoidType())
        t1 = NeuralType(('B', 'Any', 'Any'), SpectrogramType())
        t2 = NeuralType(('B', 'T', 'C'), SpectrogramType())
        self.assertEqual(t0.compare(t1), NeuralTypeComparisonResult.SAME)
        self.assertEqual(t0.compare(t2), NeuralTypeComparisonResult.SAME)
        self.assertEqual(t1.compare(t2), NeuralTypeComparisonResult.SAME)
        self.assertEqual(t2.compare(t1), NeuralTypeComparisonResult.INCOMPATIBLE)
        self.assertEqual(t1.compare(t0), NeuralTypeComparisonResult.INCOMPATIBLE)

    @pytest.mark.unit
    def test_struct(self):
        class BoundingBox(ElementType):
            def __str__(self):
                return "bounding box from detection model"

            def fields(self):
                return ("X", "Y", "W", "H")

        # ALSO ADD new, user-defined, axis kind
        class AxisKind2(AxisKindAbstract):
            Image = 0

        T1 = NeuralType(
            elements_type=BoundingBox(),
            axes=(
                AxisType(kind=AxisKind.Batch, size=None, is_list=True),
                AxisType(kind=AxisKind2.Image, size=None, is_list=True),
            ),
        )

        class BadBoundingBox(ElementType):
            def __str__(self):
                return "bad bounding box from detection model"

            def fields(self):
                return ("X", "Y", "H")

        T2 = NeuralType(
            elements_type=BadBoundingBox(),
            axes=(
                AxisType(kind=AxisKind.Batch, size=None, is_list=True),
                AxisType(kind=AxisKind2.Image, size=None, is_list=True),
            ),
        )
        self.assertEqual(T2.compare(T1), NeuralTypeComparisonResult.INCOMPATIBLE)
