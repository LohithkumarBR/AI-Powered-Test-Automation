import base64
import io
import re
import xml.etree.ElementTree as ET
from PIL import Image
import cv2
import os
import time
from find_icon_coords import find_element_index
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
class Screenshot:
    def parse_bounds(self,bstr):
            nums = re.findall(r"\d+", bstr)
            return tuple(map(int, nums)) if len(nums) == 4 else None
    def take_clean_screenshot(self,driver, save_path,xml):

        screenshot_base64 = driver.get_screenshot_as_base64()
        img_data = base64.b64decode(screenshot_base64)
        image = Image.open(io.BytesIO(img_data))
        width, height = image.size

        # xml_source=driver.page_source
        tree = ET.fromstring(xml)

        all_bounds = []
        for node in tree.iter():
            b = node.attrib.get("bounds")
            if not b:
                continue
            coords = self.parse_bounds(b)
            if not coords:
                continue
            x1, y1, x2, y2 = coords

            clazz = node.attrib.get("class", "")
            rid = node.attrib.get("resource-id", "")

            # Skip invisible or wrapper containers that fill the whole screen
            if (y2 - y1) < 15:  # too small, likely divider/line
                continue
            if clazz in ["android.widget.FrameLayout", "android.widget.LinearLayout", "android.view.ViewGroup"] and rid == "":
                continue  # skip unidentifiable layout wrappers

            all_bounds.append((x1, y1, x2, y2))

        if not all_bounds:
            logger.info(" No meaningful bounds found; saving full screenshot.")
            image.save(save_path)
            return

        # Step 3: Compute top & bottom bounds based on visible UI area
        # top_bound = min(y1 for (_, y1, _, _) in all_bounds)
        bottom_bound = max(y2 for (_, _, _, y2) in all_bounds)

        if bottom_bound > (height * 0.98):  # root might include nav bar area
            # Find the next highest visible element (ignoring root)
            candidate_bottoms = sorted(set(y2 for (_, _, _, y2) in all_bounds if y2 < height * 0.98))
            if candidate_bottoms:
                bottom_bound = candidate_bottoms[-1]

        # Step 5: Add small safe margins (optional but recommended)
        top_bound =0
        bottom_bound = min(height, bottom_bound + 3)

        # Step 6: Crop and save final clean image
        cropped = image.crop((0, top_bound, width, bottom_bound))
        cropped.save(save_path)

    def rects_intersect(self, r1, r2):
        return not (r1[2] <= r2[0] or r1[0] >= r2[2] or r1[3] <= r2[1] or r1[1] >= r2[3])

    def find_free_position(self, x, y, w, h, text_w, text_h, img_w, img_h, used_positions):
        padding = 4
        gap = 6
        candidates = []
        candidates.append((x, y - text_h - gap))
        candidates.append((x + w - text_w, y - text_h - gap))
        candidates.append((x - text_w - gap, y))
        candidates.append((x - text_w - gap, y + h - text_h))
        candidates.append((x + w + gap, y))
        candidates.append((x + w + gap, y + h - text_h))
        candidates.append((x, y + h + gap))
        candidates.append((x + w - text_w, y + h + gap))

        for (lx, ly) in candidates:
            lx, ly = int(lx), int(ly)
            rect = (
                lx - padding,
                ly - padding,
                lx + text_w + padding,
                ly + text_h + padding,
            )
            if rect[0] < 0 or rect[1] < 0 or rect[2] > img_w or rect[3] > img_h:
                continue
            if any(self.rects_intersect(rect, u) for u in used_positions):
                continue
            used_positions.append(rect)
            return lx, ly
        return None

    def draw_xml_boxes_with_index(self,image_path, xml_source, output_path):
        # Load the image
        img = cv2.imread(image_path)
        img_h, img_w = img.shape[:2]

        tree = ET.fromstring(xml_source)
        root = tree

        # Extract all bounds
        boxes = []
        for elem in root.iter():
            if ('bounds' in elem.attrib) and ((elem.attrib.get('clickable') == 'true'and elem.attrib.get('enabled') == 'true') or
                                            any(w in elem.attrib.get('class') for w in ["edittext", "autocompletetextview"]) ):

                bounds = elem.attrib['bounds']
                coords = [int(num) for num in bounds.replace('][', ',').replace('[', '').replace(']', '').split(',')]
                boxes.append(coords)

        used_positions = []
        for idx, (x1, y1, x2, y2) in enumerate(boxes):
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 3)

            label = str(idx + 1)
            font_scale = 1.2
            thickness = 2
            font = cv2.FONT_HERSHEY_SIMPLEX
            (text_w, text_h), baseline = cv2.getTextSize(label, font, font_scale, thickness)
            
            w = x2 - x1
            h = y2 - y1

            pos = self.find_free_position(x1, y1, w, h, text_w, text_h, img_w, img_h, used_positions)
            
            if pos:
                # lx, ly = pos
                # Put text at calculated position
                cv2.putText(img, label, (x1 + 8, y1 + 14), font, font_scale, (0, 0, 0), thickness, cv2.LINE_AA)

                # cv2.putText(img, label, (lx, ly + text_h), font, font_scale, (0, 0, 0), thickness, cv2.LINE_AA)
            else:
                # Fallback to inside top-left
                cv2.putText(img, label, (x1 + 8, y1 + 14), font, font_scale, (0, 0, 0), thickness, cv2.LINE_AA)

        cv2.imwrite(output_path, img)
        # logger.info(f" Saved indexed image at: {output_path}")
        return boxes


    def centers_from_boxes(self,boxes):
        centers = []
        for (x1, y1, x2, y2) in boxes:
            cx = (x1 + x2) / 2.0
            cy = (y1 + y2) / 2.0
            centers.append((cx, cy))
        return centers


    def main(self,step,filtered_steps,driver,xml_source,keyword,action=None,input_value=None,element_type=None,element_name=None):
        # Take clean screenshot
        start_time = time.time() 
        folder_path = "img"
        os.makedirs(folder_path, exist_ok=True)

        self.take_clean_screenshot(driver, "img/cropped_exact.png",xml_source)

        SCREENSHOT_PATH = "img/cropped_exact.png"
        OUTPUT_PATH = "img/numbered_boxes_final.png"

        # Verify input files
        if not xml_source:
            logger.info(" XML not found")
            return []
        if not os.path.exists(SCREENSHOT_PATH):
            logger.info(f" Screenshot not found: {SCREENSHOT_PATH}")
            return []

        clickable_boxes=self.draw_xml_boxes_with_index(SCREENSHOT_PATH, xml_source, OUTPUT_PATH)

        centers = self.centers_from_boxes(clickable_boxes)
        result,memory,input_tokens,completion_tokens,total_tokens=find_element_index(driver,step,filtered_steps,centers,clickable_boxes,xml_source,keyword,action=action,input_value=input_value,element_type=element_type,element_name=element_name)

        end_time = time.time()
        total_time = end_time - start_time
        logger.info(f" Total execution time: {total_time:.2f} seconds")
        return result,memory,input_tokens,completion_tokens,total_tokens


