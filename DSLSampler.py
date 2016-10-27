import os
import random
import json
import subprocess
import pickle
import copy


def get_postconditions(prog_str, preconditions):
    # Note that each call to subprocess has ~10ms overhead, so 1m calls costs 3 hours
    # To lessen this cost, we batch the calls per program, which is a 100x improvement
    temp_file = '/home/juesato/code/temp.py'

    python_file = 'import pickle as _pickle; import sys as _sys;\n'
    preconditions_str = pickle.dumps(preconditions)
    # TODO: Precondition pickle should be passed as argument
    python_file += '_precond_str = """{0}""";\n'.format(preconditions_str)
    python_file += '_preconds = _pickle.loads(_precond_str);\n'
    python_file += """
_postconds = []
for _precond in _preconds:
    try:
        _init_str = ''
        for _k, _v in _precond.iteritems():
            _init_str += _k + '=' + str(_v) + ';'
        exec(_init_str)
        {0}
        _all_vars = vars().copy()
        _state={{}};
        for _k in _all_vars:
            if not _k.startswith('_'):
                _state[_k] = _all_vars[_k]
                del _k
    except Exception as _e:
        _postconds.append(None)
        continue
    _postconds.append(_state)
print _pickle.dumps(_postconds)

""".format(prog_str)
    # for precondition in preconditions:
    #     init_lines = ''
    #     for k, v in precondition.iteritems():
    #         init_lines += '{0}={1};\n'.format(k, str(v))
    #     python_file += init_lines
    #     python_file += prog_str
    #     python_file += print_state_and_clear


    # cmd = 'printf "{0}" | python'.format(python_file)
    with open(temp_file, 'w') as f:
        f.write(python_file)
    cmd = 'python {0}'.format(temp_file)
    states_as_str = subprocess.check_output(cmd, shell=True)
    # print states_as_str
    # print "MADE IT"
    try:
        return pickle.loads(states_as_str)
    except Exception as e:
        with open('/home/juesato/code.txt', 'w') as f:
         f.write(states_as_str)
         print "ERROR"


class ProgramSampler:

    """
    Specifies a program uniformly at randomly from the following grammar:
    s = s_1;s_2; | f
    f = e_1 + e_2 | e_1 - e_2 | e_1 * e_2 | e_1 / e_2 | e_1 % e_2
    e = v | n
    v = x | y | z | t
    n is an integer
    """

    MX_INPUT_INT = 1000
    OPS = ['+', '-', '*', '/']

    def __init__(self, symbols):
        self.symbols = symbols

    def sample_program(self, prog_len, start_symbols):
        """
        Samples a program randomly from the specified grammar. The program has
        length `prog_len` and samples a program which modifies variables in 
        `symbols`, where the initially defined variables are given by 
        `start_symbols`.
        """
        in_scope = start_symbols
        prog = ''
        for i in xrange(prog_len):
            lh_symbol = random.choice(self.symbols)
            rh_symbol1 = random.choice(in_scope)
            rh_symbol2 = random.choice(in_scope)
            op = random.choice(ProgramSampler.OPS)

            if lh_symbol not in in_scope:
                in_scope.append(lh_symbol)
            line_str = lh_symbol + '=' + rh_symbol1 + op + rh_symbol2 + ';'
            prog += line_str
        return prog

    def sample_inputs(self, start_symbols):
        """
        Sample inputs as random integers from start_symbols
        """
        precondition = {}
        for symbol in start_symbols:
            precondition[symbol] = random.randint(-ProgramSampler.MX_INPUT_INT,
                                                  ProgramSampler.MX_INPUT_INT)
        return precondition

    def sample_io(self, start_symbols, prog_str):
        precondition = self._sample_inputs(start_symbols)
        state = copy.deepcopy(precondition)
        postcondition = get_postcondition(prog_str, state)
        return {'pre': precondition,
                'post': postcondition}


class DatasetWriter:
    PROG_INTERVAL = 100

    def __init__(self, prog_sampler):
        self.prog_sampler = prog_sampler

    def create_dataset(self, data_dir, mx_len, num_progs,
                       num_samples_per_prog):
        for i in xrange(1, mx_len+1):
            file_path = os.path.join(data_dir, 'len' + str(i) + '.json')
            print "Writing to {0}".format(file_path)
            with open(file_path, 'w') as out_file:
                out_file.write('[\n')
                prog_count = 0
                while prog_count < num_progs:
                    if not prog_count % DatasetWriter.PROG_INTERVAL:
                        print "PROG COUNT", prog_count
                    start_symbols = self._sample_start_symbols()
                    prog = self.prog_sampler.sample_program(
                        i, copy.deepcopy(start_symbols))

                    in_examples = []
                    for j in xrange(num_samples_per_prog * 2):
                        in_examples.append(self.prog_sampler.sample_inputs(start_symbols))
                    out_examples = get_postconditions(prog, in_examples)

                    # io_examples = []
                    # num_attempts = 0
                    # # Some programs often have / by 0 errors
                    # bad_program = False
                    # while len(io_examples) < num_samples_per_prog:
                    #     num_attempts += 1
                    #     if num_attempts > num_samples_per_prog * 2:
                    #         bad_program = True
                    #         break
                    #     try:
                    #         sample_io = self.prog_sampler.sample_io(
                    #             start_symbols, prog)
                    #     except Exception as e:
                    #         # Probably hit an error due to divide by 0
                    #         # print e
                    #         continue
                    #     io_examples.append(sample_io)

                    # if bad_program:
                    #     continue

                    prog_count += 1
                    data_pt = {
                        'source_code': prog,
                        # 'io_examples': io_examples
                        'io_examples': zip(in_examples, out_examples)
                    }
                    out_file.write(
                        json.dumps(data_pt, indent=4,
                                   separators=(',', ': '),
                                   sort_keys=True))
                    out_file.write(',\n')
                out_file.write(']')

    def _sample_start_symbols(self):
        start_symbols = []
        for symbol in self.prog_sampler.symbols:
            if not len(start_symbols):
                start_symbols.append(symbol)
            elif random.random() > 0.5:
                start_symbols.append(symbol)
        return start_symbols
