from DSLSampler import ProgramSampler, DatasetWriter

# Configs
DATA_DIR = '/home/juesato/code/prog_data'
# NUM_PROGS = 10000
# NUM_SAMPLES_PER_PROG = 100
NUM_PROGS = 2
NUM_SAMPLES_PER_PROG = 3
MAX_PROG_LENGTH = 4
SYMBOLS = ['x','y','z','t']

sampler = ProgramSampler(SYMBOLS)
writer = DatasetWriter(sampler)
writer.create_dataset(DATA_DIR, MAX_PROG_LENGTH, NUM_PROGS, NUM_SAMPLES_PER_PROG)
