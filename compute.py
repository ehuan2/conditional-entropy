import argparse

from grammar import PCFG
from entropy import calc_inside, conditional_entropy
from utils import entropy


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--sentence', '-s', type=str)
    parser.add_argument('--grammar', '-g', type=str)
    parser.add_argument('--root', '-r', type=str, default='S')
    args = parser.parse_args()
    args.sentence = args.sentence.split()

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

    output_title = 'Prob               \t\t Entropy                \t Word'
    output_format = '{:.15f} \t\t {:.15f} \t {:s}'
    
    print(output_title)
    print(output_format.format(
            1.0, grammar.node_entropy[grammar.nt2idx[args.root]], '**START**'
        )
    )
    for i in range(len(probs_notend)):
        prob_notend = probs_notend[i]
        ent_notend = ents_notend[i]
        prob_end = p[grammar.nt2idx[args.root]][0][i]
        ent_end = h[grammar.nt2idx[args.root]][0][i]
        prob = prob_notend + prob_end

        ent = prob_end / prob * ent_end + prob_notend / prob * ent_notend + \
            entropy(([prob_end / prob] if prob_end > 0 else []) +
                [prob_notend / prob] if prob_notend > 0 else [])
        print(output_format.format(prob, ent, args.sentence[i]))
