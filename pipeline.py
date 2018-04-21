import logging
import csv
import numpy as np
import cv2
import matplotlib.pyplot as plt

from coba import fieldnames, filelog


#=================================== Menentukan warna wilayah deteksi ==================================================
AREA_COLOR = (66, 183, 42)
#HLS
#=============================================== Write CSV =============================================================
fieldnames = ['time', 'capacity', 'hasil']
filelog = 'report.csv'

def reset():
    with open(filelog, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
reset()

def write(time, count, conclution):
    with open(filelog, 'a', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writerow({fieldnames[0]: time, fieldnames[1]: count, fieldnames[2]: conclution
         })
#=======================================================================================================================

#==================================== Menentukan kesimpulan traffic ====================================================
def conclution(hasil):
    if hasil >= 100:
        hsl = 'padat'
    elif hasil < 100 and hasil >= 75:
        hsl = 'padat merayap'
    elif hasil < 75 and hasil >= 50:
        hsl = 'ramai lancar'
    elif hasil < 50 and hasil >= 25:
        hsl = 'senggang'
    else:
        hsl = 'sepi'

    return hsl
#=======================================================================================================================

#==================================== Class PipelineRunner sebagai pemanggil class =====================================
class PipelineRunner(object):
    def __init__(self, pipeline=None, log_level=logging.DEBUG):
        #def __init__ untuk membuat fungsi untuk mendefinisikan fungsi baru
        #logging.DEBUG sebagai penyimpan data yang sudah diproses
        self.pipeline = pipeline or []
        self.context = {}
        #objek yang mendefinisikan context runtime yang ditetapkan saat menyatakan pernyataan
        self.log = logging.getLogger(self.__class__.__name__)
        #objek yang digunakan untuk menyimpan data
        self.log.setLevel(log_level)
        #objek yang digunakan untuk membrikan ambang batas proses yang dikerjakan
        self.log_level = log_level
        self.set_log_level()

    def set_context(self, data):
        self.context = data
        #inisialisasi self.context sebagai data

    def add(self, processor):
        if not isinstance(processor, PipelineProcessor):
        #isinstance adalah sebuah fungsi untuk melihat apakah processor merupakan turunan dari PipelineProcessor
            raise Exception(
                'Processor should be an isinstance of PipelineProcessor.')
        processor.log.setLevel(self.log_level)
        self.pipeline.append(processor)

    def remove(self, name):
    #fungsi yang digunakan untuk menghitung ulang proses ketika program dijalankan kembali (enumerate)
        for i, p in enumerate(self.pipeline):
            if p.__class__.__name__ == name:
                del self.pipeline[i]
                return True
        return False

    def set_log_level(self):
        for p in self.pipeline:
            p.log.setLevel(self.log_level)

    def run(self):
        #funsi yang digunakan untuk menyatakan keterangan process yang berjalan
        for p in self.pipeline:
            self.context = p(self.context)

        self.log.debug("Frame #%d processed.", self.context['frame_number'])

        return self.context
#=======================================================================================================================

#============================== Class untuk menyimpan setiap process yang sudah berjalan ===============================
class PipelineProcessor(object):
    '''
        Base class for processors.
    '''

    def __init__(self):
        self.log = logging.getLogger(self.__class__.__name__)
#=======================================================================================================================

#===================================== Class untuk menghitung kendaraan ================================================
class CapacityCounter(PipelineProcessor):

    def __init__(self, area_mask, save_image=False, image_dir='./'):
        super(CapacityCounter, self).__init__()

        self.area_mask = area_mask
        self.all = np.count_nonzero(area_mask)
        self.image_dir = image_dir
        self.save_image = save_image
        self.vehicle_count=0


    def calculate_capacity(self, frame, frame_number):
        base_frame = frame

        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        #mengubah frame kedalam filter abu abu

        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        cll = clahe.apply(frame)
        # CLAHE (Contrast Limited Adaptive Histogram Equaliztion)
        # digunakan untuk mengurangi noise dengan menambahkan brigthness

        edges = cv2.Canny(frame,50,70)
        #cv2.canny digunakan untuk menentukan batas tepi dari gambar

        edges = ~edges
        blur = cv2.bilateralFilter(cv2.blur(edges, (21,21), 100),9,200,200)
        #mengubah image menjadi lowpastfilter (memperlembut) untuk mengurangi noise pada gambar edge
        #nilai ancor (21,21), x=100, y=200

        _, threshold = cv2. threshold(blur,230, 255,cv2.THRESH_BINARY)
        #memilah pixel berdasarkan nilai threshold

        t = cv2.bitwise_and(threshold,threshold,mask = self.area_mask)


        free = np.count_nonzero(t)
        capacity = 1 -float(free)/self.all

        if self.save_image:
        #mengatur tamoilan dari gambar
            img = np.zeros(base_frame.shape, base_frame.dtype)
            img[:, :] = AREA_COLOR
            mask = cv2.bitwise_and(img, img, mask=self.area_mask)
            #operasi and,or untuk memberikan tambahan judul gambar

            cv2.addWeighted(mask, 1, base_frame, 1, 0, base_frame)
            #untuk menggabungkan dua gambar

            fig = plt.figure()
            fig.suptitle("Capacity: {}%".format(capacity*100), fontsize=12)
            write(frame_number, capacity*100, conclution(capacity))
            print('nilai kesimpulan: ',conclution(capacity*100))
            plt.subplot(211),plt.imshow(base_frame),plt.title(('gambar asli'), fontsize=12)
            #letak gambar asli berada diatas dengan sumbu simetri 211
            plt.xticks([]), plt.yticks([])
            plt.subplot(212),plt.imshow(t),plt.title(('gambar setelah diproses'), fontsize=12)
            #letak gambar setelah diproses berada di bawah dengan sumbu simetri 212
            plt.xticks([]), plt.yticks([])

            fig.savefig(self.image_dir + ("/process_%s.png" % frame_number),  dpi=500)

        return capacity

    def __call__(self, context):
        frame = context['frame'].copy()
        frame_number = context['frame_number']

        capacity = self.calculate_capacity(frame, frame_number)

        self.log.debug("Capacity: {}%".format(capacity*100))
        context['capacity'] = capacity

        return context
#=======================================================================================================================