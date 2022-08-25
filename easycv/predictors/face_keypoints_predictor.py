# Copyright (c) Alibaba, Inc. and its affiliates.

import copy
import os

import cv2
import numpy as np
import torch
from torchvision.transforms import Compose

from easycv.datasets.registry import PIPELINES
from easycv.models import build_model
from easycv.predictors.builder import PREDICTORS
from easycv.predictors.interface import PredictorInterface
from easycv.utils.checkpoint import load_checkpoint
from easycv.utils.config_tools import mmcv_config_fromfile
from easycv.utils.registry import build_from_cfg
from ..models import *
from .base import PredictorV2

face_contour_point_index = [
    0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
    21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32
]
left_eye_brow_point_index = [33, 34, 35, 36, 37, 38, 39, 40, 41, 33]
right_eye_brow_point_index = [42, 43, 44, 45, 46, 47, 48, 49, 50, 42]
left_eye_point_index = [66, 67, 68, 69, 70, 71, 72, 73, 66]
right_eye_point_index = [75, 76, 77, 78, 79, 80, 81, 82, 75]
nose_bridge_point_index = [51, 52, 53, 54]
nose_contour_point_index = [55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65]
mouth_outer_point_index = [84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 84]
mouth_inter_point_index = [96, 97, 98, 99, 100, 101, 102, 103, 96]


@PREDICTORS.register_module()
class FaceKeypointsPredictor(PredictorV2):
    """Predict pipeline for face keypoint
    Args:
        model_path (str): Path of model path
        model_config (str): config file path for model and processor to init. Defaults to None.
    """

    def __init__(self,
                 model_path,
                 model_config,
                 batch_size=1,
                 device=None,
                 save_results=False,
                 save_path=None,
                 mode='bgr'):
        super(FaceKeypointsPredictor, self).__init__(
            model_path,
            model_config,
            batch_size=batch_size,
            device=device,
            save_results=save_results,
            save_path=save_path,
            mode=mode)

        self.input_size = self.cfg.IMAGE_SIZE
        self.point_number = self.cfg.POINT_NUMBER

    def show_result(self, img, points, scale=4.0, save_path=None):
        """Draw `result` over `img`.

        Args:
            img (str or Tensor): The image to be displayed.
            result (Tensor): The face keypoints to draw over `img`.
            scale: zoom in or out scale
            save_path: path to save drawned 'img'
        Returns:
            img (Tensor): Only if not `show` or `out_file`
        """

        img = cv2.imread(img)
        img = img.copy()
        h, w, c = img.shape
        scale_h = h / self.input_size
        scale_w = w / self.input_size

        points = points.view(-1, self.point_number, 2).cpu().numpy()[0]
        for index in range(len(points)):
            points[index][0] *= scale_w
            points[index][1] *= scale_h

        image = cv2.resize(img, dsize=None, fx=scale, fy=scale)

        def draw_line(point_index, image, point):
            for i in range(len(point_index) - 1):
                cur_index = point_index[i]
                next_index = point_index[i + 1]
                cur_pt = (int(point[cur_index][0] * scale),
                          int(point[cur_index][1] * scale))
                next_pt = (int(point[next_index][0] * scale),
                           int(point[next_index][1] * scale))
                cv2.line(image, cur_pt, next_pt, (0, 0, 255), thickness=2)

        draw_line(face_contour_point_index, image, points)
        draw_line(left_eye_brow_point_index, image, points)
        draw_line(right_eye_brow_point_index, image, points)
        draw_line(left_eye_point_index, image, points)
        draw_line(right_eye_point_index, image, points)
        draw_line(nose_bridge_point_index, image, points)
        draw_line(nose_contour_point_index, image, points)
        draw_line(mouth_outer_point_index, image, points)
        draw_line(mouth_inter_point_index, image, points)

        size = len(points)
        for i in range(size):
            x = int(points[i][0])
            y = int(points[i][1])
            cv2.putText(image, str(i), (int(x * scale), int(y * scale)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            cv2.circle(image, (int(x * scale), int(y * scale)), 2, (0, 255, 0),
                       cv2.FILLED)

        if save_path is not None:
            cv2.imwrite(save_path, image)

        return image
