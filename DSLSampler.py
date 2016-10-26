import os
import random
import json


class ProgramEnv:

    """
    Defines which variables in the current Python scope we care about
    var_names: a list of strings
    """

    def __init__(self, var_names):
        self.var_names = var_names

    def get_state(self):
        state = {}
        all_vars = vars()
        for v in self.var_names:
            # Look at global value
            global t
            exec('global ' + v)
            print ("MAKE", 'global ' + v)
            print "HELP", all_vars
            print "V", v
            if v in all_vars:
                state[v] = all_vars[v]
        return state

    def clear_state(self):
        for v in self.var_names:
            del v

    def set_state(self, inp):
        assert(type(inp) == type({}),
               'set_state takes a dict of variable names and values as input')
        for k in inp:
            v = inp[k]
            # TODO: Is this the best way to do this
            setter = 'global ' + k + ';' + k + '=' + str(v)
            print "INIT", setter
            exec(setter)


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
        self.program_env = ProgramEnv(symbols)

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

    def _sample_inputs(self, start_symbols):
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
        self.program_env.clear_state()
        self.program_env.set_state(precondition)
        print("PROGR", prog_str)
        print("PRECO", precondition)
        exec(prog_str)
        postcondition = self.program_env.get_state()
        return {'precondition': precondition,
                'postcondition': postcondition}


class DatasetWriter:

    def __init__(self, prog_sampler):
        self.prog_sampler = prog_sampler

    def create_dataset(self, data_dir, mx_len, num_progs, num_samples_per_prog):
        for i in xrange(1, mx_len+1):
            file_path = os.path.join(data_dir, 'len' + str(i) + '.json')
            with open(file_path, 'w') as out_file:
                out_file.write('[\n')
                for j in xrange(num_progs):
                    start_symbols = self._sample_start_symbols()
                    prog = self.prog_sampler.sample_program(i, start_symbols)
                    io_examples = []
                    while len(io_examples) < num_samples_per_prog:
                        try:
                            sample_io = self.prog_sampler.sample_io(
                                start_symbols, prog)
                        except Exception:
                            # Probably hit an error due to divide by 0
                            continue
                        io_examples.append(sample_io)

                    data_pt = {
                        'source_code': prog,
                        'io_examples': io_examples
                    }
                    out_file.write(
                        json.dumps(data_pt, indent=4, separators=(',', ': ')))
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
