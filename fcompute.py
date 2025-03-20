import argparse
import json

from grammar import PCFG
from entropy import calc_inside, conditional_entropy
from utils import entropy


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', '-i', type=str)
    parser.add_argument('--output', '-o', type=str)
    parser.add_argument('--grammar', '-g', type=str)
    parser.add_argument('--root', '-r', type=str, default='S')
    args = parser.parse_args()

    args.sentence = open(args.input).readlines()[0].strip().split()

    grammar = PCFG(args.grammar)
    print(f'Finished building grammar')
    grammar.reorganize()
    print(f'Finished reorganizing grammar')
    grammar.calc_entropy()
    print(f'Finished calculating entropy')
    p, h = calc_inside(grammar, args.sentence)
    print(f'Finished calc_inside')
    probs_notend, ents_notend = conditional_entropy(
        grammar, p, h, len(args.sentence), args.root
    )
    print(f'Finished conditional_entropy')

    probs = list([1.0])
    ents = list([grammar.node_entropy[grammar.nt2idx[args.root]]])
    ent_red = list()
    for i in range(len(probs_notend)):
        prob_notend = probs_notend[i]
        ent_notend = ents_notend[i]
        prob_end = p[grammar.nt2idx[args.root]][0][i]
        ent_end = h[grammar.nt2idx[args.root]][0][i]
        prob = prob_notend + prob_end
        ent = prob_end / prob * ent_end + prob_notend / prob * ent_notend + \
            entropy(([prob_end / prob] if prob_end > 0 else []) +
                [prob_notend / prob] if prob_notend > 0 else [])
        probs.append(prob)
        ent_red.append(ent - ents[-1])
        ents.append(ent)
    
    with open(args.output, 'w') as fout:
        fout.write(json.dumps(
            {
                'sentence': ' '.join(args.sentence), 
                'prob': probs,
                'entropy': ents,
                'entropy_reduction': ent_red
            }
        ) + '\n')
        fout.close()
