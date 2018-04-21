import os
import logging
import logging.handlers
import random
import time
import numpy as np
import skvideo.io
import cv2
import utils



cv2.ocl.setUseOpenCL(True)
random.seed(123)



#================================================================================

IMAGE_DIR = "./out"
VIDEO_SOURCE = "input.mp4"
SHAPE= (720, 1280)
AREA_PTS =np.array([[780, 716], [686, 373], [883, 383], [1280, 636], [1280, 720]])

from pipeline import (
    PipelineRunner,
    CapacityCounter
    )

#===============================================================================


def main():
    log = logging.getLogger("main")

    #membuat titik area, dimana kendaraan akan dihitung========================

    base = np.zeros(SHAPE + (3,), dtype = 'uint8')
    area_mask = cv2.fillPoly(base, [AREA_PTS], (255, 255, 255))[:, :, 0]

    pipeline =  PipelineRunner(pipeline=[
        CapacityCounter(area_mask=area_mask, save_image=True, image_dir=IMAGE_DIR),
        # saving every 10 seconds
        ], log_level=logging.DEBUG)

   #mengatur sumber gambar diambil============================================
          
    cap= skvideo.io.vreader(VIDEO_SOURCE)

    frame_number = -1
    st = time.time()
    for frame in cap:
        if not frame.any():
            log.error("frame capture failed, stopping....")
            
    #nomor frame asli========================================================
            
        frame_number += 1
            

        pipeline.set_context({
            'frame': frame,
            'frame_number': frame_number,
            })
        context = pipeline.run()
        
    #skipping 10 second====================================================

        for i in range(240):
            cap.__next__()

#=========================================================================
        

if __name__ == "__main__":
    log = utils.init_logging()

    if not os.path.exists(IMAGE_DIR):
        log.debug("Creating image directory '&s'...", IMAGE_DIR)
        os.makedirs(IMAGE_DIR)

    main()