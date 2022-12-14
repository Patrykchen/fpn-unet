import os

import numpy as np
import cv2

from PIL import Image
from tqdm import tqdm

from unet import Unet


def get_miou(gt,pre):
    gt_flatten = gt.flatten()
    pre_flatten = pre.flatten()

    gt_count = np.bincount(gt_flatten)
    pre_count = np.bincount(pre_flatten)

    catagory = 2 * gt_flatten + pre_flatten
    cm1d = []

    for index in range(4):
        tmp = np.where(catagory == index, 1, 0)
        total = np.sum(tmp)
        cm1d.append(total)

    I  = np.array([cm1d[0],cm1d[-1]])
    U = np.array(gt_count + pre_count - I)
    IoU = I / U
    miou = np.nanmean(IoU)

    return miou


def mask_to_boundary(mask, dilation_ratio=0.1):
    h, w = mask.shape
    img_diag = np.sqrt(h ** 2 + w ** 2)  # 计算图像对角线长度
    dilation = int(round(dilation_ratio * img_diag))
    if dilation < 1:
        dilation = 1

    mask = mask.astype(np.uint8)
    # Pad image so mask truncated by the image border is also considered as boundary.
    new_mask = cv2.copyMakeBorder(mask, 1, 1, 1, 1, cv2.BORDER_CONSTANT, value=0)
    kernel = np.ones((3, 3), dtype=np.uint8)
    new_mask_erode = cv2.erode(new_mask, kernel, iterations=dilation)

    # 因为之前向四周填充了0, 故而这里不再需要四周
    mask_erode = new_mask_erode[1: h + 1, 1: w + 1]

    # G_d intersects G in the paper.
    return mask - mask_erode


def boundary_iou(gt, dt, dilation_ratio=0.05, cls_num=2):

    gt = gt.astype(np.uint8)
    gt = np.squeeze(gt,axis=0)
    dt = dt.astype(np.uint8)

    boundary_iou_list = []
    for i in range(cls_num):

        gt_i = (gt == i)
        dt_i = (dt == i)

        gt_boundary = mask_to_boundary(gt_i, dilation_ratio)
        dt_boundary = mask_to_boundary(dt_i, dilation_ratio)
        intersection = ((gt_boundary * dt_boundary) > 0).sum()
        union = ((gt_boundary + dt_boundary) > 0).sum()
        if union < 1:
            boundary_iou_list.append(0)
            continue
        boundary_iou = intersection / union
        boundary_iou_list.append(boundary_iou)

    return np.nanmean(np.array(boundary_iou_list))
