import copy
import importlib.util
import itertools
import random
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('support_prune', HERE / 'prune.py')
prune = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prune)


class PruneTests(unittest.TestCase):
    @staticmethod
    def all_selections(catalog):
        """Tiny Cartesian oracle; checks reachability independently of search."""
        packages, roots = prune.resolver.validate(catalog)
        names = sorted(packages)
        options = [[None, *packages[name]] for name in names]
        solutions = set()
        for values in itertools.product(*options):
            selected = {name: value for name, value in zip(names, values)
                        if value is not None}
            if any(name not in selected or
                   not prune.resolver.accepts(selected[name], constraint)
                   for name, constraint in roots.items()):
                continue
            reached = set()
            pending = list(roots)
            valid = True
            while pending:
                name = pending.pop()
                if name in reached:
                    continue
                reached.add(name)
                for target, constraint in packages[name][selected[name]].items():
                    if (target not in selected or
                            not prune.resolver.accepts(selected[target], constraint)):
                        valid = False
                        break
                    pending.append(target)
                if not valid:
                    break
            if valid and reached == set(selected):
                solutions.add(tuple(sorted(selected.items())))
        return solutions

    def test_chain_propagates_and_does_not_mutate_input(self):
        catalog = {'packages': {'a': {'1': {'b': '>=2'}},
                                'b': {'1': {'c': '*'}},
                                'c': {'1': {}}}, 'roots': {'a': '*'}}
        original = copy.deepcopy(catalog)
        result = prune.prune(catalog)
        self.assertEqual(catalog, original)
        self.assertEqual(result['status'], 'proven_unsatisfiable')
        self.assertEqual([(r['package'], r['dependency']) for r in result['removed']],
                         [('a', 'b')])

    def test_root_exclusion_cascades(self):
        catalog = {'packages': {'a': {'1': {}, '2': {}},
                                'b': {'1': {'a': '==1'}}},
                   'roots': {'a': '==2', 'b': '*'}}
        result = prune.prune(catalog)
        self.assertEqual(result['status'], 'proven_unsatisfiable')
        self.assertEqual(result['retained_releases'], 1)
        self.assertEqual(result['removed'], [
            {'package': 'a', 'release': '1', 'source': 'root', 'constraint': '==2'},
            {'package': 'b', 'release': '1', 'source': 'dependency',
             'dependency': 'a', 'constraint': '==1'}])

    def test_long_chain_and_missing_target(self):
        catalog = {'packages': {}, 'roots': {'p0': '*'}}
        for i in range(101):
            catalog['packages'][f'p{i}'] = {'1': {f'p{i+1}': '*'}}
        result = prune.prune(catalog)
        self.assertEqual(result['retained_releases'], 0)
        self.assertEqual(len(result['removed']), 101)
        self.assertEqual(result['status'], 'proven_unsatisfiable')

    def test_supported_cycle_survives(self):
        catalog = {'packages': {'a': {'1': {'b': '*'}},
                                'b': {'1': {'a': '*'}}}, 'roots': {'a': '*'}}
        result = prune.prune(catalog)
        self.assertEqual(result['removed'], [])
        self.assertEqual(result['reduced_catalog'], catalog)
        self.assertEqual(prune.resolver.solve(catalog)['status'], 'resolved')

    def test_local_support_does_not_claim_global_solution(self):
        catalog = {'packages': {'a': {'1': {'c': '==1'}},
                                'b': {'1': {'c': '==2'}},
                                'c': {'1': {}, '2': {}}},
                   'roots': {'a': '*', 'b': '*'}}
        result = prune.prune(catalog)
        self.assertEqual(result['status'], 'not_proven_unsatisfiable')
        self.assertEqual(result['removed'], [])
        self.assertEqual(prune.resolver.solve(catalog)['status'], 'unsatisfiable')

    def test_random_equivalence_against_complete_solver(self):
        rng = random.Random(34)
        names = ('a', 'b', 'c')
        specs = ('*', '==1', '==2', '>=2', '<2', '!=1')
        for _ in range(300):
            packages = {}
            for name in names:
                packages[name] = {}
                for release in ('1', '2'):
                    deps = {target: rng.choice(specs) for target in names
                            if rng.randrange(4) == 0}
                    packages[name][release] = deps
            catalog = {'packages': packages,
                       'roots': {name: rng.choice(specs) for name in names
                                 if rng.randrange(3) == 0}}
            if not catalog['roots']:
                catalog['roots'] = {'a': '*'}
            result = prune.prune(catalog)
            before = prune.resolver.solve(catalog, max_steps=100000)
            after = prune.resolver.solve(result['reduced_catalog'], max_steps=100000)
            self.assertEqual(before['status'], after['status'])
            self.assertEqual(self.all_selections(catalog),
                             self.all_selections(result['reduced_catalog']))
            if before['status'] == 'resolved':
                self.assertEqual(before['selected'], after['selected'])

    def test_real_metadata_projection(self):
        data = prune.resolver.load(
            HERE.parent / 'offline-resolver' / 'examples' / 'requests.json')
        result = prune.prune(data)
        self.assertEqual(result['original_releases'], 10)
        self.assertEqual(result['retained_releases'], 8)
        self.assertEqual(prune.resolver.solve(data)['status'],
                         prune.resolver.solve(result['reduced_catalog'])['status'])


if __name__ == '__main__':
    unittest.main()
