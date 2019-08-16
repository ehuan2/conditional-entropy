# PCFG Conditional Entropy Calculator

A fast, easy-to-install and parallelable PCFG conditional probability and conditional entropy calculator. 



Beta version. If something went wrong, please first check the [FAQs](#FAQs) if the something went wrong. <br>
Feel free to [contact the author](mailto:freda@ttic.edu) or directly raise an issue in this repo if you had questions or comments. 

## Dependencies
Python >= 3.7 <br>
scipy >= 1.2.1 <br>

## Demo
```
python compute.py -s "Jon hit the dog with a stick" -g ./data/strauss.pcfg
```

## FAQs
- Why the entropy/probability is Nan? <br>
    - Check if all words in your sentences appear in your given grammar. 

- Why RuntimeError? <br>
    - Check if the given grammar is *consistent* (i.e., the probability of all generated sentences from the root node `S` sums up to 1). The current system does not support inconsistent grammars. 
    - Check if there is left recursion in your grammar using ``check_left_recursion.py``. For more details about why removing left recursions, see [Hale (2003)](http://www.umiacs.umd.edu/~ymarton/ling849b/hale2003.pdf). 

- Does the current calculator support empty terminal?
    - No, but it is possible to extend it by simply modifying some code in `calc_inside` and `conditional_entropy`.

## Acknowledgement
This tool calculates PCFG conditional entropy defined by [Hale(2003)](http://www.umiacs.umd.edu/~ymarton/ling849b/hale2003.pdf), as [CCPC](https://github.com/timhunter/ccpc) does. 
The example data are from [CCPC](https://github.com/timhunter/ccpc).