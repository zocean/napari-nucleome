import os
import h5py
import numpy as np

def is_hdf5(filename):
    if not os.path.isfile(filename):
        return False
    try:
        with h5py.File(filename,'r') as hdf:
            pass
        return True
    except:
        return False


def generate_fake_data(filename):
    """
    Generate fake HDF5 data for testing purposes.
    HDF5
      - probes 
        - probe_type
          - meta
            * probe_count: (int32) # number of probes, reserved item
            (*) source: (S64) # URL or URI 
          - pos
            probe_id: (S64)
            chrom: (S64)
            start: (int32)
            end: (int32)
            allele: (S64)
          - zxy
            (n, z, y, x) # z, y, x coordinates  (float64, float64, float64)
      - targets
        - meta
          * image_count: (int32)
        - data
          target_image_1: (n, z, y, x) # target image 1: (int32, int32, int32) -> float64
          target_image_2: (n, z, y, x) # target image 2: (int32, int32, int32) -> float64
    """
    from scipy import ndimage
    np.random.seed(0)
    l = 50
    # generate nicely looking random 3D volumeric data
    image_count = 1
    vol = np.zeros((l, l, l))
    pts = (l * np.random.rand(3, l//2)).astype(int)
    vol[tuple(indices for indices in pts)] = 1
    vol = ndimage.gaussian_filter(vol, 4)
    vol /= vol.max() 
    vol = vol * 2.5
    # generate probes
    probe_count = 50
    probe_xyz = np.array([np.random.uniform(0, l, probe_count) for _ in range(3)], dtype='float64')
    probe_id = ['probe_%d' % (i) for i in range(probe_count)]
    probe_chrom = list(np.random.choice(['chr1', 'chr2', 'chr3', 'chr4', 'chr5'], probe_count))
    probe_start = np.array(np.random.randint(0, 200, probe_count), dtype='int32') * 1000000
    probe_end = probe_start + 200000
    probe_allele = ['A' for _ in range(probe_count)]
    # write to hdf5 
    with h5py.File(filename, 'w') as hdf:
        # add probes
        hdf.create_group('probes')
        hdf['probes'].create_group('probe_demo')
        hdf['probes']['probe_demo'].create_group('meta')
        hdf['probes']['probe_demo'].create_group('pos')
        hdf['probes']['probe_demo'].create_group('xyz')
        hdf['probes']['probe_demo']['meta'].create_dataset('probe_count', data=probe_count, dtype='int32')
        hdf['probes']['probe_demo']['zxy'].create_dataset('data', data=probe_xyz, dtype='float64')
        hdf['probes']['probe_demo']['pos'].create_dataset('probe_id', data=probe_id, dtype=h5py.string_dtype('utf-8'))
        hdf['probes']['probe_demo']['pos'].create_dataset('chrom', data=probe_chrom, dtype=h5py.string_dtype('utf-8'))
        hdf['probes']['probe_demo']['pos'].create_dataset('start', data=probe_start, dtype='int32')
        hdf['probes']['probe_demo']['pos'].create_dataset('end', data=probe_end, dtype='int32')
        hdf['probes']['probe_demo']['pos'].create_dataset('probe_allele', data=probe_allele, dtype='int32')
        # add image 
        hdf.create_group('targets')
        hdf['targets'].create_group('meta')
        hdf['targets'].create_group('data')
        hdf['targets']['meta'].create_dataset('image_count', data = image_count, dtype='int32')
        hdf['targets']['data'].create_dataset('target_image_1', data=vol, dtype='float64')


     