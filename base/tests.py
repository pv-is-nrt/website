from types import SimpleNamespace
from unittest import TestCase

from .views import _get_cv_proposal_groups


class CvProposalGroupsTests(TestCase):
    def test_groups_proposals_in_status_order(self):
        proposals = [
            SimpleNamespace(status='not funded', title='Declined'),
            SimpleNamespace(status='funded', title='Awarded'),
            SimpleNamespace(status='pending', title='Under review'),
        ]

        groups = _get_cv_proposal_groups(proposals)

        self.assertEqual(
            [group['label'] for group in groups],
            ['Funded', 'Pending', 'Not funded'],
        )
        self.assertEqual(
            [group['proposals'][0].title for group in groups],
            ['Awarded', 'Under review', 'Declined'],
        )

    def test_omits_empty_status_groups(self):
        groups = _get_cv_proposal_groups([
            SimpleNamespace(status='pending', title='Under review'),
        ])

        self.assertEqual([group['label'] for group in groups], ['Pending'])
