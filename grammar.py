import json
import math
import numpy as np 
from scipy.sparse import csc_matrix
from scipy.sparse.linalg import inv

from utils import entropy


"""the production (rule) class"""
class Production(object):
    def __init__(self, prod_str):
        prod = prod_str[:prod_str.find('[')].split()
        self.lhs = prod[3]
        if prod[-2] == '-->':
            self.rhs = (prod[-1],)
            self.unary = True
        else:
            self.rhs = (prod[-2], prod[-1])
            self.unary = False
        self.prob = float(prod[0]) / float(prod[2])  # TODO(fhs): improve accuracy
        self.lexical = self.unary and (prod[-1][0] == prod[-1][-1] == '"')
        if self.lexical:
            self.rhs = (self.rhs[0][1:-1], )
    
    def __str__(self):
        return json.dumps(
            {
                'lhs': self.lhs,
                'rhs': self.rhs,
                'unary': self.unary,
                'lexical': self.lexical,
                'prob': self.prob
            }
        )

    def __repr__(self):
        return self.__str__()


"""the main PCFG class"""
class PCFG(object):
    def __init__(self, file_name):
        self.productions = list()
        self.non_lexical_prods = list()
        self.lexical_prods = list()
        lines = open(file_name).readlines()
        for line in lines:
            self.productions.append(Production(line.strip('[')))
        for production in self.productions:
            # print(production)
            if production.lexical:
                self.lexical_prods.append(production)
            else:
                self.non_lexical_prods.append(production)
        self.productions_by_node = dict()
        self.non_lexical_prods_by_node = dict()
        self.nt2idx = dict()    # non-terminal to index
        self.idx2nt = list()    # index to non-terminal
        self.basic_entropy = list()

    """assuming there is no left cycle, do topological sort"""
    def _topological_sort(self, productions):
        in_cnt = np.zeros(len(self.idx2nt), dtype=np.int32)
        sorted_prods = list()
        non_terminals = list()
        for production in productions:
            rhs = production.rhs[0]
            in_cnt[self.nt2idx[rhs]] += 1
        candidates = list()
        for i, non_terminal in enumerate(self.idx2nt):
            if in_cnt[i] == 0:
                candidates.append(non_terminal)
        # queue, do BFS
        while len(candidates) != 0:
            candidate = candidates[0]
            non_terminals.append(candidate)
            for production in self.productions_by_node[candidate]:
                if production.lexical:
                    continue
                sorted_prods.append(production)
                rhs = production.rhs[0]
                in_cnt[self.nt2idx[rhs]] -= 1
                if in_cnt[self.nt2idx[rhs]] == 0:
                    candidates.append(rhs)
            candidates = candidates[1:]
        for item in self.idx2nt:
            if item not in non_terminals:
                non_terminals.append(item)
        sorted_prods.reverse()
        non_terminals.reverse()
        return sorted_prods, non_terminals
    
    def __getitem__(self, index):
        return self.productions[index]

    def __len__(self):
        return len(self.productions)
    
    """reorganize by non-terminal nodes, assign idxs to nodes"""
    def reorganize(self):
        for production in self.productions:
            lhs = production.lhs
            rhs = production.rhs

            if lhs not in self.productions_by_node:
                self.productions_by_node[lhs] = list()

            self.productions_by_node[lhs].append(production)
            if production.lexical:
                continue
            if rhs[0] not in self.productions_by_node:
                self.productions_by_node[rhs[0]] = list()
            if len(rhs) == 2 and rhs[1] not in self.productions_by_node:
                self.productions_by_node[rhs[1]] = list()

        print(len(self.productions_by_node))

        for node in self.productions_by_node:
            self.idx2nt.append(node)
            idx = len(self.nt2idx)
            self.nt2idx[node] = idx

        # topological sort for the non-lexical productions
        self.non_lexical_prods, self.idx2nt = self._topological_sort(self.non_lexical_prods)
        for idx, node in enumerate(self.idx2nt):
            self.nt2idx[node] = idx
        for node in self.idx2nt:
            self.non_lexical_prods_by_node[node] = list()
            if node not in self.productions_by_node:
                self.productions_by_node[node] = list()
            for production in self.productions_by_node[node]:
                if not production.lexical:
                    self.non_lexical_prods_by_node[node].append(production)

    """calculate entropy for each node"""
    def calc_entropy(self):
        # basic entropy
        for node in self.idx2nt:
            probs = list()
            for production in self.productions_by_node[node]:
                probs.append(production.prob)
            self.basic_entropy.append(entropy(probs))

        print("Finished calculating basic entropy")
        # sparse matrix for (I-A), where H = (I-A)^{-1} h
        mat_dict = dict()
        for i in range(len(self.idx2nt)):
            mat_dict[(i, i)] = 1

        print("Finished the matrix dictionary multiplication")


        for node in self.idx2nt:
            for production in self.non_lexical_prods_by_node.get(node, []):
                left_idx = self.nt2idx[node]
                for right_node in production.rhs:
                    right_idx = self.nt2idx[right_node]
                    if (left_idx, right_idx) not in mat_dict:
                        mat_dict[(left_idx, right_idx)] = 0
                    mat_dict[(left_idx, right_idx)] -= production.prob

        print("Finished populating the matrix dicitonary multiplication")

        rows = list()
        cols = list()
        data = list()

        for left_idx, right_idx in mat_dict:
            rows.append(left_idx)
            cols.append(right_idx)
            data.append(mat_dict[(left_idx, right_idx)])
        print("Finished the matrix dictionary appending to rows and columns")
        
        mat_dict = None
        
        matrix = csc_matrix((data, (rows, cols)), 
            shape=(len(self.idx2nt), len(self.idx2nt)))
        
        print(len(self.idx2nt))
        print(f"Matrix is finished...")
        matrix = inv(matrix)
        print(f"Matrix inverse calculated")
        self.node_entropy = matrix * np.array(self.basic_entropy)
        print(f"Calculated the basic entropy")


"""unit test"""
if __name__ == "__main__":
    sentence = "Mr. Pierre Vinken , 61 years old , will join this group"
    grammar = PCFG('./data/rlr_800.wmcfg')
    grammar.reorganize()
    grammar.calc_entropy()
    from IPython import embed
    embed(using=False)
