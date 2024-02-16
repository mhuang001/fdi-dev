# -*- coding: utf-8 -*-

from .common import trbk
from fdi.dataset.mediawrapper import MediaWrapper
from fdi.dataset.numericparameter import NumericParameter
from fdi.dataset.arraydataset import ArrayDataset

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

use_pypng = 1
use_fpnge = 0


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
nn,n    6: RGBA (4 channels)
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


def toPng(adset, grey=False, compression=0, cspace=8, cmap=None,
          png_file_name=None, return_medw=False, return_bin=False,
          verbose=False):
    """ Make a PNG an image from an `ArrayDataset`.

    Parameters
    ----------
    adset : list, ArrayDataset,
        Any Sequence of Sequence of 2byte data.
    grey : bool
        Grey scale for pixel values clipped to [median-3stdev,
    median+3stdev] then mapped to full grey range, if set `True`
    (default) else RGB color of sorted unique pixel values
    scaled to full color space.
    compression : int
        0-9 for how much to compress. default to 0 for no compression
    cspace : int
        Frim 1 to 16 for bits per channel. 16 for grey 8 for color.
    cmap : dict
        An ordered dictionary that gives (R,G,B) for a pixel value.
    default is `longrainbowl`.
    """
    #__import__("pdb").set_trace()


    # add color legend
    if issubclass(adset.__class__, ArrayDataset):
        data = adset.data
    else:
        data = adset

    if not data:
        return b''
    height = len(data)
    width = len(data[0])
    tcode = getattr(adset, 'typecode', 'H')[0]
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

        if png_file_name:
            if use_pypng:
                with open(png_file_name+'.png', 'wb') as f:
                    w = png.Writer(width, height, greyscale=grey,
                                   bitdepth=bitdepth, compression=compression)
                    w.write(f, img)
            else:
                # use_fpnge is True or not
                if img[0].typecode[0] in [unsigned_tc, 'h'] and sys.byteorder == 'little':
                    for i in img:
                        i.byteswap()
                if png_file_name:
                    with open(png_file_name+'.png', 'wb') as b:
                        b.write(generate_png(img, width, height, greyscale=grey,
                                             bitdepth=bitdepth, compression=compression))
        else:
            if return_bin:
                bf = b''.join(x.tobytes() for x in data)
                return bf
            # with open(fnm+'.bin', 'wb') as b:
            #        pb.write(bf)
            return generate_png(img, width, height, greyscale=grey,
                                bitdepth=bitdepth, compression=compression)

    if cmap is None:
        cmap = longrainbowl(cspace)

    uniq_vals = list(set(chain.from_iterable(data)))
    if len(uniq_vals) == 0:
        return b''
    
    uniq_vals.sort()
    nuniq_vals = len(uniq_vals)
    scl = float(ncolor)/nuniq_vals
    # color normalization table that maps a pixel value to a color index in cmap
    cnt = dict((c, int(i*scl)) for i, c in enumerate(uniq_vals))
    if use_pypng:
        cmap2 =  dict((c, cmap[int(i*scl)]) for i, c in enumerate(uniq_vals))
    if use_fpnge:
        # bytes
        cmap3 =  dict((c, bytes(cmap[int(i*scl)])) for i, c in enumerate(uniq_vals))
    wlscale = nuniq_vals/float(width)

#    _r = range(-(width//2), (width//2)
#               ) if tcode in ['h', 'b'] else range(width)
    uv = [uniq_vals[int(x*wlscale)] for x in range(width)]

    clegend = [array.array(tcode, uv)]*color_legend_height

    height += color_legend_height
    #__import__("pdb").set_trace()

    t1 = time.time()
    cng = cnt.__getitem__

    if use_fpnge:
        cmg3 = cmap3.__getitem__

        r = bytearray(b'')
        rs = r.__setitem__
        re = r.extend
        list(map(re, map(cmg3,
                chain.from_iterable(
                    chain(data, clegend))
                         )
                 )
             )
        img = memoryview(r)
    elif 0:
        # concatenate: all r, then all g, then all b
        ln_ = width * height
        ln_2 = ln_ * 2
        r, g, b = bytearray([]), bytearray([]), bytearray([])
        #r = bytearray(ln_ * 3)
        #cmg2 = cmap2.__getitem__
        rs = r.__setitem__
        ra, ga, ba = r.append, g.append, b.append
        n = 0
        for i, j, k in map(cmg2, chain.from_iterable(
                               chain(data, clegend))
                           ):

            #rs(n,i)
            #rs(n+ln_,j)
            #rs(n+ln_2,k)
            ra(i)
            ga(j)
            ba(k)
            n += 1
        r.extend(g)
        r.extend(b)
        img = memoryview(r) #bytes(r)

        print(time.time()-t1)
        if 0:
            print( data[0][:10])
            print(list(cnt[x] for x in data[0][:10]))
            print(list(cmap[cnt[x]] for x in data[0][:10]))
            print(list(zip(*list(cmap[cnt[x]] for x in data[0][:10]))))
            print(img[:10])
            
    elif use_pypng:
        
        if 0:  # 29.0
            # def mkb(row): return bytes(map(cnt.__getitem__, row))
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
                #map(lambda row:array.array('B', map(cng, row)),
                map(lambda row: bytes(map(cng, row)),
                    chain(data, clegend)
                    )
                )
        elif 0:
            # 39sec
            img = list(
                array.array('B', (cnt[x] for x in row))
                for row in chain(data, clegend))
    else:  # 39sec
        # python
        img = list(
                map(
                    lambda row: array.array('B', map(cng, row)),
                    chain(data, clegend)
                )
            )
                
    if 0:
        print(nuniq_vals, 'values in', len(cmap), 'colors')
        li = list(chain.from_iterable(img))
        print('mlc90', max(li), len(li), len(set(list(li))),
              list(map(hex, li[:7])), (data[0][0]-mean)/stdev)

    if issubclass(img[0].__class__, array.array) and img[0].typecode[0] in ['H', 'h'] and sys.byteorder == 'little':
        for i in img:
            i.byteswap()

    if use_fpnge:
        import fpnge
        png_im = fpnge.fromview(
            view=img,
            width=width,
            height=height,
            channels=3,
            bits_per_channel=8,
            stride=width*3
        )
    elif 0:
        import fpng_py as fpp
        # not working. always "invalid parameters"
        print(fpp.fpng_cpu_supports_sse41())
        png_im = fpp.fpng_encode_image_to_memory(
            #filename=png_file_name+'.png',
            image=img,
            w=width,
            h=height,
            num_chans=3,
            #flags=fpp.CompressionFlags.NONE #x1 if compression else 0
        )
    elif use_pypng:
        wtr = png.Writer(width, height, palette=cmap.values(),
                     bitdepth=cspace,
                     compression=compression)
        try:
            with io.BytesIO() as iob:
                wtr.write(iob, img)
                png_im = iob.getvalue()
        except png.ProtocolError as e:
            logger.error(f'{png_file_name} {width}x{height} {len(data[0])} {e} {trbk(e)}')
            return b''

    else:
        png_im = generate_png(img, width, height, greyscale=False,
                              bitdepth=8, compression=compression)
    if png_file_name:
        # if output PNG, output BIN, too.
        ##bf = b''.join(x.tobytes() for x in data)
        with open(png_file_name+'.png', 'wb') as b:
            b.write(png_im)
    if 1:
        print('png', time.time()-t1, 'sec')

    return png_im
