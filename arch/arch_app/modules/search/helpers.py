from datetime import date
import numpy as np
from arch_app.models import Record
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models.functions import Greatest
from django.db.models import Q, Case, When
from guardian.shortcuts import get_objects_for_user
from django.conf import settings
if settings.ACTIVATE_AI_SEARCH:
    from sentence_transformers import util
    from ..embeddings.text_image_embedding import generate_text_embedding


class SearchMixin():
    """
    Mixin for search view
    """

    def filter_records(self, cleaned_data):
        """
        Return a filtered queryset of records
        """
        # if the user does not provide an end date, set it to today
        if cleaned_data['start_date'] and not cleaned_data['end_date']:
            cleaned_data['end_date'] = date.today()

        filtered_records = None
        q_list = []
        # create a list of Q objects to filter the queryset

        if cleaned_data['depicted_users']:
            q_list.append(
                Q(depicted_users__user__username__icontains=cleaned_data['depicted_users']) |
                Q(depicted_users__user__first_name__icontains=cleaned_data['depicted_users']) |
                Q(depicted_users__user__last_name__icontains=cleaned_data['depicted_users'])

            )

        if cleaned_data['media_type'] != 'All':
            q_list.append(Q(type=cleaned_data['media_type']))
        if cleaned_data['start_date']:
            q_list.append(Q(date_created__range=[cleaned_data['start_date'], cleaned_data['end_date']]))
        # if the user does not provide a start date but provides an end date instead
        if cleaned_data['end_date'] and not cleaned_data['start_date']:
            q_list.append(Q(date_created__lte=cleaned_data['end_date']))

        if cleaned_data['location']:
            q_list.append(
                Q(location__name__icontains=cleaned_data['location']) |
                Q(location__country__icontains=cleaned_data['location']) |
                Q(location__state__icontains=cleaned_data['location']) |
                Q(location__region__icontains=cleaned_data['location'])
            )

        # filter the queryset based on the user's permissions
        if q_list:

            filtered_records = get_objects_for_user(self.request.user,
                                                  "view_record",
                                                  Record.objects.select_related('depicted_users').filter(Q(*q_list, _connector=Q.AND)))
        else:
            filtered_records = get_objects_for_user(self.request.user,
                                                  "view_record",
                                                  Record.objects.select_related('depicted_users').all())
        return filtered_records

    def get_search_results(self, cleaned_data):
        """
        Return ranked records
        cleaned_data: cleaned data from the search form
        """

        # apply filters here:
        filtered_records = self.filter_records(cleaned_data)

        # compute similarity scores if the user provides a search query
        if cleaned_data['search_query']:
            if settings.ACTIVATE_AI_SEARCH:
                # compute query_vector here
                query_vector = generate_text_embedding(cleaned_data['search_query'])
            else:
                query_vector = None
            records = []

            # Trigram similarity is a score between 0 and 1, hence they're mapped to [-1, 1]
            records_similarity = filtered_records.annotate(
                similarity_title=2 * (TrigramSimilarity('title', cleaned_data['search_query'])) - 1,
                # normalize to [-1, 1], replace 3 with number of fields
                similarity_location=2 * (Greatest(
                    TrigramSimilarity('location__name', cleaned_data['search_query']),
                    TrigramSimilarity('location__country', cleaned_data['search_query']),
                    TrigramSimilarity('location__state', cleaned_data['search_query']),
                    TrigramSimilarity('location__region', cleaned_data['search_query'])
                )) - 1,
                # weight location higher
                similarity_caption=2 * (TrigramSimilarity('user_caption', cleaned_data['search_query'])) - 1,

            )

            for record in records_similarity:
                if record.embedding is None or query_vector is None:
                    similarity_query = -1
                else:
                    # similarity score is between -1 and 1
                    similarity_query = util.cos_sim(query_vector, np.array(record.embedding, dtype=np.float32))
                    similarity_query = similarity_query.item()

                similarity_title = record.similarity_title if record.similarity_title is not None else -1
                similarity_location = record.similarity_location if record.similarity_location is not None else -1
                similarity_caption = record.similarity_caption if record.similarity_caption is not None else -1

                sum_similarity = similarity_title + similarity_location + similarity_caption + similarity_query
                # take max in case sum_similarity is negative
                total_similarity = max(sum_similarity, similarity_title, similarity_location, similarity_caption,
                                       similarity_query)

                # add 0.2 to total_similarity if the user is depicted in the record
                for depicted_u in record.depicted_users.user_set.all():
                    username = depicted_u.username.lower() if depicted_u.username else ''
                    first_name = depicted_u.first_name.lower() if depicted_u.first_name else ''
                    last_name = depicted_u.last_name.lower() if depicted_u.last_name else ''
                    search_query = cleaned_data['search_query'].lower()
                    if username in search_query or first_name in search_query or last_name in search_query:
                        # if the query only contains the username, first_name or last_name, add 0.2 to the similarity score. This ensures that the record item is shown in the search results
                        total_similarity += 0.2
                        if total_similarity > 4:
                            total_similarity = 4
                        break

                if total_similarity > 0.2:
                    records.append({
                        'id': record.id,
                        'similarity': total_similarity
                    })

            # Sort items by similarity
            records = sorted(records, key=lambda x: x['similarity'], reverse=True)

            search_results_ids = [str(record['id']) for record in records]
            preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(search_results_ids)])
            search_results = filtered_records.filter(pk__in=search_results_ids).order_by(preserved)
        else:

            search_results = filtered_records
            search_results_ids = [str(r.id) for r in search_results]

        return search_results_ids, search_results
