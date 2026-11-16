from . import transform as trans
from .model_lib.MultiFTNet import MultiFTNet
import cv2, numpy as np, os, torch, torch.nn.functional as F

class AntiSpoof:
    def __init__(self, device_id=0):
        super(AntiSpoof, self).__init__()
        self.device = torch.device(f"cuda:{device_id}" if torch.cuda.is_available() else "cpu")
        self.loaded_models = {}

    def _get_model(self, model_path):
        if model_path in self.loaded_models:
            return self.loaded_models[model_path]

        model_name = os.path.basename(model_path)
        h_input, w_input, model_type, _ = parse_model_name(model_name)
        kernel_size = get_kernel(h_input, w_input)
        model = MultiFTNet(conv6_kernel=kernel_size).to(self.device)

        try:
            state_dict = torch.load(model_path, map_location=self.device, weights_only=False)
        except TypeError:
            state_dict = torch.load(model_path, map_location=self.device)

        keys = iter(state_dict)
        first_layer_name = next(keys)
        if first_layer_name.find('module.') >= 0:
            from collections import OrderedDict
            new_state_dict = OrderedDict()
            for key, value in state_dict.items():
                name_key = key[7:]
                new_state_dict[name_key] = value
            model.load_state_dict(new_state_dict)
        else:
            model.load_state_dict(state_dict)

        model.eval()
        self.loaded_models[model_path] = model
        return model

    def predict(self, img, model_path):
        test_transform = trans.Compose([trans.ToTensor()])
        tensor_img = test_transform(img).unsqueeze(0).to(self.device)
        model = self._get_model(model_path)
        with torch.no_grad():
            result = model(tensor_img)
            result = F.softmax(result, dim=1).cpu().numpy()
        return result


class CropImage:
    @staticmethod
    def _get_new_box(src_w, src_h, bbox, scale):
        x = bbox[0]
        y = bbox[1]
        box_w = bbox[2]
        box_h = bbox[3]

        scale = min((src_h - 1) / max(box_h, 1), min((src_w - 1) / max(box_w, 1), scale))

        new_width = box_w * scale
        new_height = box_h * scale
        center_x, center_y = box_w / 2 + x, box_h / 2 + y

        left_top_x = center_x - new_width / 2
        left_top_y = center_y - new_height / 2
        right_bottom_x = center_x + new_width / 2
        right_bottom_y = center_y + new_height / 2

        if left_top_x < 0:
            right_bottom_x -= left_top_x
            left_top_x = 0

        if left_top_y < 0:
            right_bottom_y -= left_top_y
            left_top_y = 0

        if right_bottom_x > src_w - 1:
            left_top_x -= right_bottom_x - src_w + 1
            right_bottom_x = src_w - 1

        if right_bottom_y > src_h - 1:
            left_top_y -= right_bottom_y - src_h + 1
            right_bottom_y = src_h - 1

        return int(left_top_x), int(left_top_y), int(right_bottom_x), int(right_bottom_y)

    def crop(self, org_img, bbox, scale, out_w, out_h, crop=True):
        if not crop:
            dst_img = cv2.resize(org_img, (out_w, out_h))
        else:
            src_h, src_w, _ = np.shape(org_img)
            left_top_x, left_top_y, right_bottom_x, right_bottom_y = self._get_new_box(src_w, src_h, bbox, scale)
            img = org_img[left_top_y:right_bottom_y + 1, left_top_x:right_bottom_x + 1]
            if img.size == 0:
                dst_img = cv2.resize(org_img, (out_w, out_h))
            else:
                dst_img = cv2.resize(img, (out_w, out_h))
        return dst_img


def parse_model_name(model_name):
    info = model_name.split('_')[0:-1]
    h_input, w_input = info[-1].split('x')
    model_type = model_name.split('.pth')[0].split('_')[-1]
    if info[0] == "org":
        scale = None
    else:
        scale = float(info[0])
    return int(h_input), int(w_input), model_type, scale


def get_kernel(height, width):
    return ((height + 15) // 16, (width + 15) // 16)
