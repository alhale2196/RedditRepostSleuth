import json
from unittest import TestCase, mock
from unittest.mock import MagicMock

from redditrepostsleuth.core.db.databasemodels import MonitoredSub
from redditrepostsleuth.core.services.responsebuilder import ResponseBuilder


class TestResponseBuilder(TestCase):
    def test_build_sub_repost_comment_custom_nosig_nostat(self):
        sub_repo = MagicMock()
        uow = MagicMock()
        uowm = MagicMock()
        sub_repo.get_by_sub.return_value = MonitoredSub(
            repost_response_template='test {total_searched} {post_type} {search_time}\n\n')
        type(uow).monitored_sub = mock.PropertyMock(return_value=sub_repo)
        uow.__enter__.return_value = uow
        uowm.start.return_value = uow
        response_builder = ResponseBuilder(uowm)
        msg_values = {
            'total_searched': 10,
            'post_type': 'image',
            'search_time': 5,
            'match_count': 5,
            'times_word': 'times',
            'first_seen': 'test',
            'oldest_percent_match': '100',
            'last_seen': 'test',
            'newest_percent_match': '100',
            'post_shortlink': 'https://redd.it/1234',
            'stats_searched_post_str': 'search str',
            'total_posts': 100,
            'false_positive_data': '{"post": "https://redd.it/1234", "meme_template": 10}'
        }
        expected = 'test 10 image 5\n\n' \
                   'search str | **Indexed Posts:** 100 | **Search Time:** 5s \n\n' \
                   '*Feedback? Hate? Visit r/repostsleuthbot - I\'m not perfect, but you can help. Report ' \
                   '[ [False Positive](https://www.reddit.com/message/compose/?to=RepostSleuthBot&subject=False%20Positive&message={"post": "https://redd.it/1234", "meme_template": 10}) ]*'
        result = response_builder.build_sub_repost_comment('test', msg_values, 'image', signature=True, stats=True)
        self.assertEqual(expected, result)

    def test_build_sub_repost_comment_custom_bad_slug(self):
        sub_repo = MagicMock()
        uow = MagicMock()
        uowm = MagicMock()
        sub_repo.get_by_sub.return_value = MonitoredSub(
            repost_response_template='test {total_searched} {fake_slug} {post_type} {search_time}\n\n')
        type(uow).monitored_sub = mock.PropertyMock(return_value=sub_repo)
        uow.__enter__.return_value = uow
        uowm.start.return_value = uow
        response_builder = ResponseBuilder(uowm)
        msg_values = {
            'total_searched': 10,
            'post_type': 'image',
            'search_time': 5,
            'match_count': 5,
            'times_word': 'times',
            'first_seen': 'test',
            'oldest_percent_match': '100',
            'last_seen': 'test',
            'newest_percent_match': '100',
            'post_shortlink': 'https://redd.it/1234',
            'stats_searched_post_str': 'search str',
            'total_posts': 100,
            'false_positive_data': '{"post": "https://redd.it/1234", "meme_template": 10}'
        }
        expected = 'Looks like a repost. I\'ve seen this image 5 times. \n\n' \
                    'test 100 match. test 100 match \n\n'
        result = response_builder.build_sub_repost_comment('test', msg_values, 'image', signature=False, stats=False)
        self.assertEqual(expected, result)

    def test_build_sub_repost_comment_custom_sig_stat(self):
        sub_repo = MagicMock()
        uow = MagicMock()
        uowm = MagicMock()
        sub_repo.get_by_sub.return_value = MonitoredSub(
            repost_response_template='test {total_searched} {post_type} {search_time}\n\n')
        type(uow).monitored_sub = mock.PropertyMock(return_value=sub_repo)
        uow.__enter__.return_value = uow
        uowm.start.return_value = uow
        response_builder = ResponseBuilder(uowm)
        expected = 'test 10 image 5\n\n'
        result = response_builder.build_sub_repost_comment('test',
                                                       {'total_searched': 10, 'post_type': 'image', 'search_time': 5,
                                                        'post_shortlink': 'http://redd.it/1234'}, 'image', signature=False, stats=False)
        self.assertEqual(expected, result)

    def test_build_default_repost_comment_nostat_nosig_multimatch(self):
        response_builder = ResponseBuilder(MagicMock())
        expected = 'Looks like a repost. I\'ve seen this image 5 times. \n\n' \
                         'test 100 match. test 100 match \n\n'
        msg_values = {
            'total_searched': 10,
            'post_type': 'image',
            'search_time': 5,
            'match_count': 5,
            'times_word': 'times',
            'first_seen': 'test',
            'oldest_percent_match': '100',
            'last_seen': 'test',
            'newest_percent_match': '100'
        }
        result = response_builder.build_default_repost_comment(msg_values, 'image', signature=False, stats=False)
        self.assertEqual(expected, result)

    def test_build_default_repost_comment_stat_nosig_onematch(self):
        response_builder = ResponseBuilder(MagicMock())
        expected = 'Looks like a repost. I\'ve seen this image 1 time. \n\n' \
                         'test 100 match. \n\n'
        msg_values = {
            'total_searched': 10,
            'post_type': 'image',
            'search_time': 5,
            'match_count': 1,
            'times_word': 'time',
            'first_seen': 'test',
            'oldest_percent_match': '100',
            'last_seen': 'test',
            'newest_percent_match': '100'
        }
        result = response_builder.build_default_repost_comment(msg_values, 'image', signature=False, stats=False)
        self.assertEqual(expected, result)

    def test_build_default_repost_comment_nostat_sig(self):
        response_builder = ResponseBuilder(MagicMock())
        expected = 'Looks like a repost. I\'ve seen this image 5 times. \n\n' \
                         'test 100 match. test 100 match \n\n' \
                   '*Feedback? Hate? Visit r/repostsleuthbot - I\'m not perfect, but you can help. Report ' \
                   '[ [False Positive](https://www.reddit.com/message/compose/?to=RepostSleuthBot&subject=False%20Positive&message={"post": "https://redd.it/1234", "meme_template": 10}) ]*'
        msg_values = {
            'total_searched': 10,
            'post_type': 'image',
            'search_time': 5,
            'match_count': 5,
            'times_word': 'times',
            'first_seen': 'test',
            'oldest_percent_match': '100',
            'last_seen': 'test',
            'newest_percent_match': '100',
            'post_shortlink': 'https://redd.it/1234',
            'false_positive_data': '{"post": "https://redd.it/1234", "meme_template": 10}'
        }
        result = response_builder.build_default_repost_comment(msg_values, 'image', signature=True, stats=False)
        self.assertEqual(expected, result)

    def test_build_default_repost_comment_stat_sig(self):
        response_builder = ResponseBuilder(MagicMock())
        expected = 'Looks like a repost. I\'ve seen this image 5 times. \n\n' \
                         'test 100 match. test 100 match \n\n' \
                   'search str | **Indexed Posts:** 100 | **Search Time:** 5s \n\n' \
                   '*Feedback? Hate? Visit r/repostsleuthbot - I\'m not perfect, but you can help. Report ' \
                   '[ [False Positive](https://www.reddit.com/message/compose/?to=RepostSleuthBot&subject=False%20Positive&message={"post": "https://redd.it/1234", "meme_template": 10}) ]*'
        msg_values = {
            'total_searched': 10,
            'post_type': 'image',
            'search_time': 5,
            'match_count': 5,
            'times_word': 'times',
            'first_seen': 'test',
            'oldest_percent_match': '100',
            'last_seen': 'test',
            'newest_percent_match': '100',
            'post_shortlink': 'https://redd.it/1234',
            'stats_searched_post_str': 'search str',
            'total_posts': 100,
            'false_positive_data': '{"post": "https://redd.it/1234", "meme_template": 10}'
        }
        result = response_builder.build_default_repost_comment(msg_values, 'image', signature=True, stats=True)
        self.assertEqual(expected, result)

    def test_build_sub_oc_comment_no_sub_return_default(self):
        sub_repo = MagicMock()
        uow = MagicMock()
        uowm = MagicMock()
        sub_repo.get_by_sub.return_value = MonitoredSub()
        type(uow).monitored_sub = mock.PropertyMock(return_value=sub_repo)
        uow.__enter__.return_value = uow
        uowm.start.return_value = uow
        response_builder = ResponseBuilder(uowm)
        expected = 'There\'s a good chance this is unique! I checked 10 image posts and didn\'t find a close match\n\n'
        result = response_builder.build_sub_oc_comment('test', {'total_searched': 10, 'post_type': 'image', 'search_time': 5}, 'image', signature=False)
        self.assertEqual(expected, result)

    def test_build_sub_oc_comment_sub_custom_msg_no_sig(self):
        sub_repo = MagicMock()
        uow = MagicMock()
        uowm = MagicMock()
        sub_repo.get_by_sub.return_value = MonitoredSub(oc_response_template='test {total_searched} {post_type} {search_time}\n\n')
        type(uow).monitored_sub = mock.PropertyMock(return_value=sub_repo)
        uow.__enter__.return_value = uow
        uowm.start.return_value = uow
        response_builder = ResponseBuilder(uowm)
        expected = 'test 10 image 5\n\n'
        result = response_builder.build_sub_oc_comment('test', {'total_searched': 10, 'post_type': 'image',
                                                                'search_time': 5}, 'image', signature=False)
        self.assertEqual(expected, result)

    def test_build_sub_oc_comment_sub_custom_msg_sig(self):
        sub_repo = MagicMock()
        uow = MagicMock()
        uowm = MagicMock()
        sub_repo.get_by_sub.return_value = MonitoredSub(oc_response_template='test {total_searched} {post_type} {search_time}\n\n')
        type(uow).monitored_sub = mock.PropertyMock(return_value=sub_repo)
        uow.__enter__.return_value = uow
        uowm.start.return_value = uow
        response_builder = ResponseBuilder(uowm)
        expected = 'test 10 image 5\n\n' \
                   '*Feedback? Hate? Visit r/repostsleuthbot - I\'m not perfect, but you can help. Report ' \
                   '[ [False Negative](https://www.reddit.com/message/compose/?to=RepostSleuthBot&subject=False%20Negative&message={"post_id": 1111, "meme_template": null}) ]*'
        result = response_builder.build_sub_oc_comment('test', {'total_searched': 10, 'post_type': 'image', 'search_time': 5, 'post_shortlink': 'http://redd.it/1234', 'false_negative_data': json.dumps(
                {
                    'post_id': 1111,
                    'meme_template': None
                }
            )}, 'image' )
        self.assertEqual(expected, result)

    @mock.patch('redditrepostsleuth.core.db.uow.sqlalchemyunitofworkmanager.SqlAlchemyUnitOfWorkManager')
    def test_build_default_oc_comment_no_sig(self, uowm):
        response_builder = ResponseBuilder(uowm)
        expected = "I didn't find any posts that meet the matching requirements for r/memes. \n\nIt might be OC, it might not. Things such as JPEG artifacts and cropping may impact the results.\n\n "
        result = response_builder.build_default_oc_comment({'total_searched': 10, 'post_type': 'image', 'search_time': 5, 'this_subreddit': 'memes'}, 'image', signature=False)
        self.assertEqual(expected, result)

    @mock.patch('redditrepostsleuth.core.db.uow.sqlalchemyunitofworkmanager.SqlAlchemyUnitOfWorkManager')
    def test_build_default_oc_comment_sig(self, uowm):
        response_builder = ResponseBuilder(uowm)
        expected = "I didn't find any posts that meet the matching requirements for r/memes. " \
                   "It might be OC, it might not. Things such as JPEG artifacts and cropping may impact the results.\n\n" \

        result = response_builder.build_default_oc_comment(
            {'total_searched': 10, 'post_type': 'image', 'search_url': 'www.test.com', 'search_time': 5, 'post_shortlink': 'http://redd.it/1234', 'this_subreddit': 'memes', 'false_negative_data': json.dumps(
                {
                    'post_id': 1111,
                    'meme_template': None
                }
            )}, 'image' )
        self.assertEqual(expected, result)
