import argparse
import json
from nltk import Nonterminal, PCFG, induce_pcfg
from nltk.corpus import ptb
import pickle


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--save', type=str, default='./data/ptb.pcfg', help='pickle file')
    parser.add_argument('--collapse-unary', action='store_true', default=False)
    parser.add_argument('--cnf', action='store_true', default=False)
    parser.add_argument('--file-ids', type=int, default=2312)
    parser.add_argument('--remove-rare', action='store_true', default=False)

    args = parser.parse_args()

    productions = []
    data = ptb.fileids()[:args.file_ids]
    total_files = len(data)
    for i, item in enumerate(data):
        print(f'Processed {i+1}/{total_files} files.')
        for tree in ptb.parsed_sents(item):
            if args.collapse_unary:
                tree.collapse_unary(collapsePOS=False)    # Remove branches A->B>C into A->B+C
            if args.cnf:
                tree.chomsky_normal_form(horzMarkov=2)    # Remove A->(B,C,D) into A -> B A|<C-D>, A|<C-D> -> C D
            productions += tree.productions()
            # debug
            for production in tree.productions():
                parent = production.lhs()
                children = ' '.join([node if type(node) is str else node.unicode_repr() for node in production.rhs()])
                if children == parent.unicode_repr() and type(production.rhs()[0]) is not str:
                    tree.un_chomsky_normal_form()
                    print(tree)

    rule_cnt = dict()
    for production in productions:
        parent = str(production.lhs())
        children = ' '.join([node if type(node) is str else node.unicode_repr() for node in production.rhs()])
        lexicalized = True if (type(production.rhs()[0]) is str) else False
        if children == parent and not lexicalized:
            continue
        children = (children, lexicalized)
        if parent not in rule_cnt:
            rule_cnt[parent] = dict()
        if children not in rule_cnt[parent]:
            rule_cnt[parent][children] = 0
        rule_cnt[parent][children] += 1

    if args.remove_rare:
        for parent in rule_cnt:
            to_remove = set()
            for children in rule_cnt[parent]:
                if rule_cnt[parent][children] == 1 and children[1] is False:
                    to_remove.add(children)
            for children in to_remove:
                del rule_cnt[parent][children]
        keep = set(['S'])
        
        def find_reachable_nodes(curr_node):
            for children in rule_cnt[curr_node]:
                if children[1] is True:
                    continue
                for child in children[0].split():
                    if child not in keep:
                        keep.add(child)
                        find_reachable_nodes(child)
        find_reachable_nodes('S')
        for parent in list(rule_cnt.keys()):
            if parent not in keep:
                del rule_cnt[parent]

    for parent in rule_cnt:
        for children in list(rule_cnt[parent].keys()):  
            rule_cnt[parent]['total_cnt'] = rule_cnt[parent].get('total_cnt', 0) + rule_cnt[parent][children]
    
    with open(args.save, 'w') as fout:
        for parent in rule_cnt:
            for children in rule_cnt[parent]:
                if children != 'total_cnt':
                    if children[1] is False:
                        fout.write(f'{rule_cnt[parent][children]} / {rule_cnt[parent]["total_cnt"]} {parent} --> {children[0]}\n')
                    else:
                        fout.write(f'{rule_cnt[parent][children]} / {rule_cnt[parent]["total_cnt"]} {parent} --> {json.dumps(children[0])} \n')
    fout.close()
