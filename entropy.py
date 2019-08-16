import math 
import numpy as np
from scipy.sparse import csc_matrix
from scipy.sparse.linalg import inv, spsolve

from grammar import PCFG
from utils import entropy 


"""calculate the inside probability and entropy for a sentence"""
def calc_inside(grammar, sent):
    prob = np.zeros((len(grammar.idx2nt), len(sent), len(sent)), dtype=np.float64)
    ent = np.zeros((len(grammar.idx2nt), len(sent), len(sent)), dtype=np.float64)
    for i in range(len(sent)):
        for production in grammar.lexical_prods:
            if production.rhs[0] == sent[i]:
                prob[grammar.nt2idx[production.lhs]][i][i] += production.prob
                ent[grammar.nt2idx[production.lhs]][i][i] = 0.0
    for l in range(1, len(sent)+1):
        for i in range(len(sent)-l+1):
            j = i + l - 1
            for k, node in enumerate(grammar.idx2nt):
                cummulated_prob = 0
                for production in grammar.non_lexical_prods_by_node[node]:
                    if production.unary:  # unary
                        curr_prob = prob[grammar.nt2idx[production.rhs[0]]][i][j]
                        if curr_prob == 0:
                            continue
                        prob[k][i][j] += production.prob * curr_prob
                        ent[k][i][j] += production.prob * curr_prob * \
                            ent[grammar.nt2idx[production.rhs[0]]][i][j] + \
                            entropy([production.prob * curr_prob])
                        cummulated_prob += production.prob * curr_prob
                    else:  # binary
                        for t in range(i, j):
                            curr_prob = prob[grammar.nt2idx[production.rhs[0]]][i][t] * \
                                prob[grammar.nt2idx[production.rhs[1]]][t+1][j]
                            if curr_prob == 0:
                                continue
                            prob[k][i][j] += production.prob * curr_prob
                            ent[k][i][j] += \
                                production.prob * curr_prob * ent[grammar.nt2idx[production.rhs[0]]][i][t] + \
                                production.prob * curr_prob * \
                                ent[grammar.nt2idx[production.rhs[1]]][t+1][j] + \
                                entropy([production.prob * curr_prob])
                            cummulated_prob += production.prob * curr_prob
                if cummulated_prob != 0:
                    ent[k][i][j] = 1.0 / cummulated_prob * ent[k][i][j] + math.log(cummulated_prob) / math.log(2.0)
    return prob, ent


"""calculate the conditional entropy for a sentence"""
def conditional_entropy(grammar, prob_info, entropy_info, sent_len, root):

    def encode(source):
        return source[2]+source[1]*sent_len+source[0]*sent_len*sent_len

    # solve probability
    visit = np.zeros((len(grammar.idx2nt), sent_len, sent_len), dtype=np.bool)
    relations = dict()

    def conditional_prob(curr_node, prefix):
        if len(prefix) == 0 or visit[grammar.nt2idx[curr_node], prefix[0], prefix[-1]] == 1:
            return
        visit[grammar.nt2idx[curr_node]][prefix[0]][prefix[-1]] = 1
        code = grammar.nt2idx[curr_node], prefix[0], prefix[-1]
        relations[code] = dict({'b': 0})
        relations[code][code] = -1
        for production in grammar.productions_by_node[curr_node]:
            if production.lexical:
                continue
            elif production.unary:
                conditional_prob(production.rhs[0], prefix)
                child_code = grammar.nt2idx[production.rhs[0]], prefix[0], prefix[-1]
                if child_code not in relations[code]:
                    relations[code][child_code] = 0
                relations[code][child_code] += production.prob
            else:  # binary
                # partially occupy the left child, right child is definitely not empty
                conditional_prob(production.rhs[0], prefix)
                left_code = grammar.nt2idx[production.rhs[0]], prefix[0], prefix[-1]
                if left_code not in relations[code]:
                    relations[code][left_code] = 0
                right_prob = 1.0
                relations[code][left_code] += production.prob * right_prob
                # fully occupy the left child, and right child is NOT empty (remove the right-empty cases)
                for split_point, split_value in enumerate(prefix):
                    left_prob = prob_info[grammar.nt2idx[production.rhs[0]]][prefix[0]][split_value]
                    conditional_prob(production.rhs[1], prefix[split_point+1:])
                    if len(prefix[split_point+1:]) == 0:  # right_prob = 1
                        relations[code]['b'] -= production.prob * left_prob
                    else:  # right_prob is variable
                        right_code = grammar.nt2idx[production.rhs[1]], prefix[split_point+1], prefix[-1]
                        if right_code not in relations[code]:
                            relations[code][right_code] = 0
                        relations[code][right_code] += production.prob * left_prob

    for l in range(sent_len):
        conditional_prob(root, list(range(l+1)))

    for i in range(len(grammar.idx2nt)):
        for j in range(sent_len):
            for k in range(sent_len):
                if (i, j, k) not in relations:
                    relations[(i, j, k)] = dict({'b': 0})
                    relations[(i, j, k)][(i, j, k)] = -1
    # make sparse matrix A
    rows = list()
    cols = list()
    data = list()
    for code in relations:
        row_ind = encode(code)
        for rel_code in relations[code]:
            if rel_code == 'b':
                continue
            col_ind = encode(rel_code)
            data_point = relations[code][rel_code]
            rows.append(row_ind)
            cols.append(col_ind)
            data.append(data_point)
    A = csc_matrix((data, (rows, cols)),
                   shape=(sent_len * sent_len * len(grammar.idx2nt),
                   sent_len * sent_len * len(grammar.idx2nt)))
    # make vector b
    b = np.zeros((sent_len * sent_len * len(grammar.idx2nt), 1), dtype=np.float64)
    for code in relations:
        ind = encode(code)
        b[ind] = relations[code]['b']
    cummulated_probs = spsolve(A, b)

    visit = np.zeros((len(grammar.idx2nt), sent_len, sent_len), dtype=np.bool)
    relations = dict()

    def extract_relations(curr_node, prefix):
        if len(prefix) == 0 or visit[grammar.nt2idx[curr_node], prefix[0], prefix[-1]] == 1:
            return
        visit[grammar.nt2idx[curr_node], prefix[0], prefix[-1]] = 1
        code = grammar.nt2idx[curr_node], prefix[0], prefix[-1]
        relations[code] = dict({'b': 0})
        for production in grammar.productions_by_node[curr_node]:
            if production.lexical:
                continue
            elif production.unary:
                extract_relations(production.rhs[0], prefix)
                child_code = grammar.nt2idx[production.rhs[0]], prefix[0], prefix[-1]
                child_prob = cummulated_probs[encode(child_code)]
                if child_prob > 0:
                    relations[code]['b'] -= entropy([production.prob * child_prob])
                    if child_code not in relations[code]:
                        relations[code][child_code] = 0
                    relations[code][child_code] += production.prob * child_prob
            else:
                # partially occupy the left child, right child is definitely not empty
                extract_relations(production.rhs[0], prefix)
                left_code = grammar.nt2idx[production.rhs[0]], prefix[0], prefix[-1]
                left_prob = cummulated_probs[encode(left_code)]
                right_prob = 1.0
                right_entropy = grammar.node_entropy[grammar.nt2idx[production.rhs[1]]]
                curr_prob = left_prob * right_prob
                if curr_prob > 0:
                    relations[code]['b'] -= entropy([production.prob * curr_prob]) + \
                        production.prob * curr_prob * right_entropy
                    if left_code not in relations[code]:
                        relations[code][left_code] = 0
                    relations[code][left_code] += production.prob * curr_prob
                # fully occupy the left child, and right child is NOT empty
                for split_point, split_value in enumerate(prefix):
                    left_prob = prob_info[grammar.nt2idx[production.rhs[0]]][prefix[0]][split_value]
                    left_entropy = entropy_info[grammar.nt2idx[production.rhs[0]]][prefix[0]][split_value]
                    extract_relations(production.rhs[1], prefix[split_point+1:])
                    if len(prefix[split_point+1:]) == 0:
                        right_prob = 1
                        right_entropy = grammar.node_entropy[grammar.nt2idx[production.rhs[1]]]
                        curr_prob = left_prob * right_prob
                        if curr_prob > 0:
                            relations[code]['b'] -= entropy([production.prob * curr_prob]) + \
                                production.prob * curr_prob * (left_entropy + right_entropy)
                    else:
                        right_code = grammar.nt2idx[production.rhs[1]], prefix[split_point+1], prefix[-1]
                        right_prob = cummulated_probs[encode(right_code)]
                        curr_prob = left_prob * right_prob
                        if curr_prob > 0:
                            relations[code]['b'] -= entropy([production.prob * curr_prob]) + \
                                production.prob * curr_prob * left_entropy
                            if right_code not in relations[code]:
                                relations[code][right_code] = 0
                            relations[code][right_code] += production.prob * curr_prob
        if cummulated_probs[encode(code)] > 0:
            prob = cummulated_probs[encode(code)]
            for rel_code in relations[code]:  # including b
                relations[code][rel_code] *= 1 / prob
            relations[code]['b'] -= math.log(prob) / math.log(2.0)
        if code not in relations[code]:
            relations[code][code] = 0
        relations[code][code] -= 1

    for l in range(sent_len):
        extract_relations(root, list(range(l+1)))

    for i in range(len(grammar.idx2nt)):
        for j in range(sent_len):
            for k in range(sent_len):
                if (i, j, k) not in relations:
                    relations[(i, j, k)] = dict({'b': 0})
                    relations[(i, j, k)][(i, j, k)] = -1
    # make sparse matrix A
    rows = list()
    cols = list()
    data = list()
    for code in relations:
        row_ind = encode(code)
        for rel_code in relations[code]:
            if rel_code == 'b':
                continue
            col_ind = encode(rel_code)
            data_point = relations[code][rel_code]
            rows.append(row_ind)
            cols.append(col_ind)
            data.append(data_point)
    A = csc_matrix((data, (rows, cols)),
                   shape=(sent_len * sent_len * len(grammar.idx2nt),
                          sent_len * sent_len * len(grammar.idx2nt)))
    # make vector b
    b = np.zeros((sent_len * sent_len * len(grammar.idx2nt), 1), dtype=np.float64)
    for code in relations:
        ind = encode(code)
        b[ind] = relations[code]['b']
    cummulated_entropy = spsolve(A, b)
    return_probs = list()
    return_entropy = list()
    for i in range(sent_len):
        ind = encode((grammar.nt2idx[root], 0, i))
        prob = cummulated_probs[ind]
        ent = cummulated_entropy[ind]
        # if prob > 0:
        #     ent = 1.0 / prob * ent + math.log(prob) / math.log(2.0)
        return_probs.append(prob)
        return_entropy.append(ent)
    # from IPython import embed; embed(using=False)

    return return_probs, return_entropy


"""unit test"""
if __name__ == "__main__":
    sentence = "Mr. Pierre Vinken , 61 years old , will join this group"
    grammar = PCFG('../pcfg/data/test_800.wmcfg')
    grammar.reorganize()
    grammar.calc_entropy()
    print(len(grammar.non_lexical_prods_by_node))
    p, h = calc_inside(grammar, sentence)
    probs_notend, ents_notend = conditional_entropy(
        grammar, p, h, len(sentence.split()), 'S'
    )
    from IPython import embed
    embed(using=False)
