import argparse 
import os, sys

global stack, edges, visit

edges = dict()
visit = dict()
stack = list()


def dfs(node):
    global stack, edges, visit
    if visit[node]:
        idx = stack.index(node)
        print('You have a left recursion as follows, please check:')
        print(' -> '.join(stack[idx:] + [node]))
        exit(0)
    visit[node] = True
    stack.append(node)
    for o in edges[node]:
        dfs(o)
    visit[node] = False
    stack = stack[:-1]


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--grammar', '-g', type=str, required=True)
    parser.add_argument('--root', '-r', type=str, default='S')
    args = parser.parse_args()
    
    for line in open(args.file):
        prod = line[:line.strip().find('[')].split()
        lhs = prod[3]
        rhs = prod[-1] if prod[-2] == '-->' else prod[-2]
        if lhs not in edges:
            edges[lhs] = set()
        edges[lhs].add(rhs)
        if rhs not in edges:
            edges[rhs] = set()
        visit[lhs] = visit[rhs] = False
    dfs(args.root)
    print('Congrats! You have no left-recursion.')
