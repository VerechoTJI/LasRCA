import unittest
import numpy as np
from data_filter.CCF_AIOps_challenge_2022.service.metric_generator import MetricGenerator


class MetricNormalizationTests(unittest.TestCase):
    def test_valid_metric_matches_released_statistic_coordinates(self):
        result=MetricGenerator.zscore_values([3.46],1.1048354166666667,1.084736343945057)
        np.testing.assert_allclose(result,[2.1711862025087862])
    def test_missing_or_constant_metric_cannot_inherit_previous_values(self):
        for mean,std in ((np.nan,np.nan),(5,0)):
            np.testing.assert_array_equal(MetricGenerator.zscore_values([np.nan,5],mean,std),[0,0])
