# watches images directory for new files.
# informs the thumbnail server when a thumbnail needs to be created.
import os
import time
import socket

allowed_formats = ('JPG', 'JPEG', 'PNG')

if __name__ == '__main__':
    img_dir = '/home/dap/projects/ridiculously.moe/img/'

    while True:
        new_files = list()
        print(str(len(os.listdir(img_dir))) + " images checking...")
        for img_filename in os.listdir(img_dir):
            img_base, img_ext = os.path.splitext(img_filename)

            if img_ext[1:].upper() not in allowed_formats:
                continue  # that's not an image!

            if not os.path.isfile(
                    os.path.join(img_dir, 'thumbs', img_base + '.png')):
                # we don't have a thumbnail for this one.
                new_files.append(img_filename)


        if new_files:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(('127.0.0.1', 8767)) # arbitrary port chosen.
            for img_name in new_files:
                full_name = os.path.join(img_dir, img_name)

                if os.path.getmtime(full_name) > time.time() - 1:
                    # changed too recently. probably still being written.
                    continue
                s.send(bytes(full_name,"UTF-8") + b"\n")
                print("Processing " + full_name)
            s.close()
        time.sleep(10)
