__author__ = 'aymgal'


import numpy as np

from slitronomy.Util import util



class ModelManager(object):

    """Utility class for initializing model operators and managing model components"""

    def __init__(self, data_class, lensing_operator_class, numerics_class,
                 subgrid_res_source=1, likelihood_mask=None, thread_count=1):
        if likelihood_mask is None:
            likelihood_mask = np.ones_like(data_class.data)
        self._mask = likelihood_mask
        self._mask_1d = util.image2array(likelihood_mask)
        self._lensing_op = lensing_operator_class
        self._conv = numerics_class.convolution_class
        if self._conv is not None:
            self._conv_transpose = self._conv.copy_transpose()
        else:
            self._conv_transpose = None
        self._prepare_data(data_class, subgrid_res_source, self._mask)
        self._no_source_light = True
        self._no_lens_light = True
        self._no_point_source = True
        self._thread_count = thread_count

    def add_source_light(self, source_model_class):
        # takes the first source light profile in the model list
        self._source_light = source_model_class.func_list[0]
        if hasattr(self._source_light, 'thread_count'):
            self._source_light.thread_count = self._thread_count
        self._no_source_light = False

    def add_lens_light(self, lens_light_model_class):
        # takes the first lens light profile in the model list
        self._lens_light = lens_light_model_class.func_list[0]
        if hasattr(self._lens_light, 'thread_count'):
            self._lens_light.thread_count = self._thread_count
        self._no_lens_light = False

    def add_point_source(self):
        self._no_point_source = False

    def set_source_wavelet_scales(self, n_scales_source):
        self._n_scales_source = n_scales_source

    def set_lens_wavelet_scales(self, n_scales_lens):
        self._n_scales_lens_light = n_scales_lens

    def subtract_from_data(self, array_2d):
        """Update "effective" data by subtracting the input array"""
        self._image_data_eff = self._image_data - array_2d

    def reset_data(self):
        """cancel any previous call to self.subtract_from_data()"""
        self._image_data_eff = np.copy(self._image_data)

    def fill_masked_data(self, background_rms):
        """Replace masked pixels with background noise"""
        noise = background_rms * np.random.randn(*self._image_data.shape)
        self._image_data[self._mask == 0] = noise[self._mask == 0]
        self._image_data_eff[self._mask == 0] = noise[self._mask == 0]

    @property
    def image_data(self):
        return self._image_data

    @property
    def lensingOperator(self):
        return self._lensing_op

    @property
    def no_source_light(self):
        return self._no_source_light

    @property
    def no_lens_light(self):
        return self._no_lens_light

    @property
    def no_point_source(self):
        return self._no_point_source

    def _prepare_data(self, data_class, subgrid_res_source, mask):
        num_pix_x, num_pix_y = data_class.num_pixel_axes
        if num_pix_x != num_pix_y:
            raise ValueError("Only square images are supported")
        self._num_pix = num_pix_x
        self._num_pix_source = int(num_pix_x * subgrid_res_source)
        self._image_data = np.copy(data_class.data)
        self._image_data_eff = np.copy(self._image_data)