# -*- coding: utf-8 -*-


import struct
from math import sqrt
import png
import sys
from itertools import chain, islice, repeat, starmap
import logging
from collections import OrderedDict
from pprint import pprint
import array
import time
import io
import statistics

# create logger
logger = logging.getLogger(__name__)
# logger.debug('level %d' %  (logger.getEffectiveLevel()))


def generate_png(buf, width, height, greyscale=True, bitdepth=8, compression=9):
    """ generate a png file.

    from https://stackoverflow.com/a/19174800/13472124
    data: bigendian array of sequences
    """
    import zlib

    nchan = 1 if greyscale else 3
    nchan_byte = nchan * bitdepth//8

    ct = 0 if greyscale else 2
    """
    # ref. e.g. https://stackoverflow.com/a/25374733/13472124
    0: Grey (1 channel)
    2: RGB  (3 channels)
    3: color palette (1 channel)
    4: Grey-alpha (2 channels)
    6: RGBA (4 channels)
    """

    # reverse the vertical line order and add null bytes at the start
    # width_byte = width * nchan_byte
    # raw_data = b"".join(b'\x00' + buf[span:span + width_byte]
    #                    for span in range((height - 1) * width_byte, -1, - width_byte))

    width_pix_ch = width * nchan
    if 0:
        raw_data = b"".join(b'\x00' + bytes(buf[span:span + width_pix_ch])
                            for span in range((height - 1) * width_pix_ch, -1, - width_pix_ch))
    else:
        raw_data = b''.join(chain(
            *zip(repeat(b'\x00'), (row.tobytes() for row in buf))
        ))
    # print('RRR', raw_data[-400*nchan_byte-1: -400*nchan_byte-1+9])

    def png_pack(png_tag, data):
        chunk_head = png_tag + data
        return struct.pack("!I", len(data)) + chunk_head + struct.pack("!I", 0xFFFFFFFF & zlib.crc32(chunk_head))

    return b"".join([
        b'\x89PNG\r\n\x1a\n',
        png_pack(b'IHDR', struct.pack("!2I5B", width, height,
                                      bitdepth, ct, compression, 0, 0)),
        png_pack(b'IDAT', zlib.compress(raw_data, compression)),
        png_pack(b'IEND', b'')])


def shortrainbowl(n=8):
    """ Short rainbowl color map modified to have 4 times colors.

    ref. https://www.particleincell.com/2014/colormap/
    return a dictionary that translates 0 - 2**n-1 to (R, G, B) where R, G, B are color from 0 - 255.
    """
    t = 2**(n-8)
    s = 2**n // 4
    ret = OrderedDict((2**n-1-Y,
                       (255,          Y//t*4,             0) if Y < s else
                       (255-(Y//t-s)*4,  255,             0) if Y < 2*s else
                       (0,               255,  (Y//t-2*s)*4) if Y < 3*s else
                       (0,      255-(Y//t-3*s)*4,       255)
                       ) for Y in range(2**n-1, -1, -1)
                      )
    return ret


def longrainbowl(n=8):
    """ Short rainbowl color map modified to have 5 times colors.

    ref. https://www.particleincell.com/2014/colormap/
    return a dictionary that translates 0 - 2**n-1 to (R, G, B) where R, G, B are color from 0 - 255.
    """
    t = 2**(n-8)
    s = 2**n // 5
    ret = OrderedDict((2**n-1-Y,
                       (255,          Y//t*5,             0) if Y < s else
                       (255-(Y//t-s)*5,  255,             0) if Y < 2*s else
                       (0,               255,  (Y//t-2*s)*5) if Y < 3*s else
                       (0,      255-(Y//t-3*s)*5,       255) if Y < 4*s else
                       ((Y//t-4*s)*5,      0,           255)
                       ) for Y in range(2**n-1, -1, -1)
                      )
    return ret


use_pypng = 1


def toPng(adset, grey=False, compression=0, cspace=8, cmap=None, verbose=False):
    """ Make a PNG an image from an `ArrayDataset`.

    adset: ArrayDataset whose data is a Sequence of Sequence of 2byte data.
    grey: Grey scale for pixel values clipped to [median-3stdev, median+3stdev] then mapped to full grey range, if True (default) else RGB color of sorted unique pixel values scaled to full color space..
    compression: 0-9 for how much to compress. default to 0 for no compression
    cspace; 1-16 for bits per channel. 16 for grey 8 for color.
    cmap: an ordered dictionary that gives (R,G,B) for a pixel value. default is `longrainbowl`.
    """

    # add color legend
    data = adset.data

    height = len(data)
    width = len(data[0])
    tcode = adset.typecode[0]
    unsigned_tc = tcode.upper()
    bitdepth = 16 if tcode in ('H', 'h') else 8 if tcode in ('b', 'B') else 32
    # highest and lowest value
    highlim = 2**(bitdepth-1)-1
    lowlim = - 2**(bitdepth-1)

    # color legend band
    color_legend_height = 10
    ncolor = 2**cspace

    if grey:
        if verbose:
            t1 = time.time()
        summ = sum(chain.from_iterable(data))
        summ2 = sum(x*x for x in chain.from_iterable(data))
        maxi = max(chain.from_iterable(data))
        mini = min(chain.from_iterable(data))
        median = statistics.median(chain.from_iterable(data))
        n = sum(len(x) for x in data)
        mean = float(summ)/n
        stdev = sqrt((summ2/n-mean**2)*n/(n-1))
        if verbose:
            print('stat %f sec' % (time.time()-t1))
            # print('Smmms', n, maxi, mini, mean, stdev)
        adset.meta['maximum'] = NumericParameter(maxi)
        adset.meta['minimum'] = NumericParameter(mini)
        adset.meta['mean'] = NumericParameter(mean)
        adset.meta['median'] = NumericParameter(median)
        adset.meta['stdev'] = NumericParameter(stdev)

        ulimit = int(median + 3*stdev)
        llimit = int(median - 3*stdev)
        if ulimit > maxi:
            ulimit = maxi
        if llimit < mini:
            llimit = mini
        # print('ul', ulimit, llimit)
        wlscale = (ulimit-llimit)/float(width)
        clscale = (ulimit-llimit)/float(ncolor-1)

        # color legend
        clegend = [array.array(tcode, list(llimit+int(x*wlscale)
                                           for x in range(width)))]*color_legend_height
        height += color_legend_height
        # signed to unsigned. clip to llimit<= v <=ulimit then scale to cspace
        img = list(
            array.array(unsigned_tc, (
                ((0 if (x - llimit) < 0 else (ncolor-1) if (x - ulimit)
                  > 0 else int((x - llimit)/clscale) if clscale != 0 else ncolor//2)
                 for x in row)
            ))
            for row in chain(data, clegend))
        # print('AAAA', max(chain(*img)))
        if fnm:
            if use_pypng:
                with open(fnm+'.png', 'wb') as f:
                    w = png.Writer(width, height, greyscale=grey,
                                   bitdepth=bitdepth, compression=compression)
                    w.write(f, img)
            else:
                if img[0].typecode[0] in [unsigned_tc, 'h'] and sys.byteorder == 'little':
                    for i in img:
                        i.byteswap()
                with open(fnm+'.png', 'wb') as b:
                    b.write(generate_png(img, width, height, greyscale=grey,
                                         bitdepth=bitdepth, compression=compression))
        image_dset = MediaWrapper(data=img, description=fnm, typ_='image/png',
                                  shape=[height, width])

        return image_dset

        bf = b''.join(x.tobytes() for x in data)
        with open(fnm+'.bin', 'wb') as b:
            b.write(bf)

    if cmap is None:
        cmap = longrainbowl(cspace)

    uniq_vals = list(set(chain.from_iterable(data)))
    uniq_vals.sort()
    nuniq_vals = len(uniq_vals)
    scl = float(ncolor)/nuniq_vals
    # color normalization table that maps a pixel value to a color index in cmap
    cnt = dict((c, int(i*scl)) for i, c in enumerate(uniq_vals))

    wlscale = nuniq_vals/float(width)

#    _r = range(-(width//2), (width//2)
#               ) if tcode in ['h', 'b'] else range(width)
    uv = [uniq_vals[int(x*wlscale)] for x in range(width)]

    clegend = [array.array(tcode, uv)]*color_legend_height

    height += color_legend_height

    t1 = time.time()
    if use_pypng:
        if 0:  # 29.0
            #def mkb(row): return bytes(map(cnt.__getitem__, row))
            img = list(
                map(
                    lambda row: bytes(map(cnt.__getitem__, row)),
                    chain(data, clegend)
                )
            )
        elif 0:
            # 29.1
            def para(row): return bytes(map(cnt.__getitem__, row))
            img = list(map(para, chain(data, clegend)))
        elif 0:  # 29.0sec
            img = list(bytes(map(cnt.__getitem__, row)) for
                       row in chain(data, clegend))
        elif 1:  # 32.0
            img = list(
                array.array('B', map(cnt.get, row))
                for row in chain(data, clegend))
        else:
            # 39sec
            img = list(
                array.array('B', (cnt[x] for x in row))
                for row in chain(data, clegend))
    else:  # 39sec
        img = list(
            array.array('B', chain.from_iterable(cmap[cnt[x]] for x in row))
            for row in chain(data, clegend))

    if 0:
        print(nuniq_vals, 'values in', len(cmap), 'colors')
        li = list(chain.from_iterable(img))
        print('mlc90', max(li), len(li), len(set(list(li))),
              list(map(hex, li[:7])), (data[0][0]-mean)/stdev)

    if issubclass(img[0].__class__, array.array) and img[0].typecode[0] in ['H', 'h'] and sys.byteorder == 'little':
        for i in img:
            i.byteswap()

    if use_pypng:
        wtr = png.Writer(width, height, palette=cmap.values(),
                         bitdepth=cspace,
                         compression=compression)
        with io.BytesIO() as iob:
            wtr.write(iob, img)
            png_im = iob.getvalue()
    else:
        png_im = generate_png(img, width, height, greyscale=False,
                              bitdepth=8, compression=compression)

    if 0:
        print('p', time.time()-t1, 'sec')

    return png_im
