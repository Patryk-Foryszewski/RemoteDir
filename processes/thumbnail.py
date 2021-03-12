from multiprocessing import Process
from threading import Thread
from PIL import Image, UnidentifiedImageError
from common import mk_logger, pure_windows_path, file_ext, thumb_name, cache_path, thumb_dir
from os import path, makedirs
import rawpy
import imageio


logger = mk_logger(__name__)
ex_log = mk_logger(name=f'{__name__}-EX',
                   level=40,
                   _format='[%(levelname)-8s] [%(asctime)s] [%(name)s] [%(funcName)s] [%(lineno)d] [%(message)s]')
ex_log = ex_log.exception


class ThumbnailGenerator(Thread):

    def __init__(self, src_path, dst_path, filename=None, size=(300, 200)):
        super().__init__()
        self.thumb_name = None
        self.thumb_name = thumb_name(src_path)
        self.src_path = src_path
        self.size = size
        self.cache_path = pure_windows_path(cache_path, dst_path.strip('/'), thumb_dir)
        self.thumb_path = pure_windows_path(self.cache_path, self.thumb_name)
        self.ok = False

    def run(self):
        if self.thumb_name:
            self.generate_thumbnail()

    def generate_thumbnail(self):

        ext = file_ext(self.src_path)

        if ext in ('.pdf', '.svg'):
            return
        logger.info(f'Creating thumbnail for {ext} file')

        if not self.thumb_name:
            return

        if not path.exists(self.cache_path):
            makedirs(self.cache_path)

        try:
            im = Image.open(self.src_path)
            im.thumbnail(self.size)
            im.save(self.thumb_path)
        except UnidentifiedImageError:
            pass
        except OSError:
            pass
        except Exception as ex:
            ex_log(f'Failed to make a thumbnail {ex}')
        else:
            logger.info(f'Thumbnail for {ext} created with Image')
            self.ok = True
            return

        try:
            from moviepy.editor import VideoFileClip
            clip = VideoFileClip(self.src_path)
            clip.save_frame(self.thumb_path, t=1.00)
        except OSError:
            pass
        except Exception as ex:
            ex_log(f'Failed to make a thumbnail {type(ex)}, {ex}')
        else:
            logger.info(f'Thumbnail for {ext} created with VideoFileClip')
            self.ok = True
            return

        from rawpy._rawpy import LibRawNoThumbnailError
        from rawpy._rawpy import LibRawUnsupportedThumbnailError
        from rawpy._rawpy import LibRawIOError

        try:
            with rawpy.imread(self.src_path) as raw:
                # raises LibRawNoThumbnailError if thumbnail missing
                # raises LibRawUnsupportedThumbnailError if unsupported format
                thumb = raw.extract_thumb()
            if thumb.format == rawpy.ThumbFormat.JPEG:
                # thumb.data is already in JPEG format, save as-is
                with open(self.thumb_path, 'wb') as f:
                    f.write(thumb.data)
            elif thumb.format == rawpy.ThumbFormat.BITMAP:
                # thumb.data is an RGB numpy array, convert with imageio
                imageio.imsave(self.thumb_path, thumb.data)
        except LibRawNoThumbnailError:
            pass
        except LibRawUnsupportedThumbnailError:
            pass
        except LibRawIOError:
            pass
        except Exception as ex:
            ex_log(f'Failed to make a thumbnail {ex}')
        else:
            im = Image.open(self.thumb_path)
            im.thumbnail(self.size)
            im.save(self.thumb_path)
            logger.info(f'Thumbnail {self.thumb_name} created with rawpy')
            self.ok = True
            return


