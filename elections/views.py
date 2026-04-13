"""
Views for the elections app.

All views are Class-Based Views.  All database access uses the Django ORM.
No raw SQL queries are used anywhere in this module.

Schema notes that affect query logic
--------------------------------------
* polling_unit has no state_id.  Delta State units are reached via:
    lga_ids = Lga.objects.filter(state_id=25).values_list('lga_id', flat=True)
    PollingUnit.objects.filter(lga_id__in=lga_ids)

* announced_pu_results.polling_unit_uniqueid stores str(polling_unit.uniqueid).
  When aggregating per LGA:
    Step 1 → collect polling_unit.uniqueid integers for that lga_id
    Step 2 → cast to strings, then filter announced_pu_results

* The datetime field on both result tables is date_entered, not time_of_entry.
"""

import json
from datetime import datetime

from django.contrib import messages
from django.db import transaction
from django.db.models import Sum
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import FormView, TemplateView

from .forms import PollingUnitResultForm
from .models import AnnouncedPuResults, Lga, PollingUnit


def _delta_lga_ids():
    """Return a queryset of lga_id values belonging to Delta State."""
    return Lga.objects.filter(state_id=25).values_list('lga_id', flat=True)


class HomeView(TemplateView):
    """
    Landing page for the Bincom Election Results Portal.

    Renders a hero section and three feature cards linking to each
    functional page of the application.
    """

    template_name = 'elections/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Home'
        return context


class PollingUnitResultsView(TemplateView):
    """
    Question 1 — View election results for a single polling unit.

    GET (no params)  : Render a dropdown of all Delta State polling units.
    GET (?polling_unit_uniqueid=X) : Fetch and display results for unit with
                                     polling_unit.uniqueid == X, including a
                                     Chart.js horizontal bar chart.
    """

    template_name = 'elections/polling_unit.html'

    def get_context_data(self, **kwargs):
        """
        Build context for the polling unit results page.

        Always provides the full list of Delta State polling units for the
        dropdown.  When a uniqueid is supplied in the query string, fetches
        results and serialises chart data as JSON.
        """
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Polling Unit Results'

        # All Delta State polling units for the dropdown
        context['polling_units'] = (
            PollingUnit.objects
            .filter(lga_id__in=_delta_lga_ids())
            .order_by('polling_unit_name')
        )

        # The query param is the polling_unit.uniqueid stored as a string
        selected_uniqueid = self.request.GET.get('polling_unit_uniqueid', '').strip()
        context['selected_uniqueid'] = selected_uniqueid

        if not selected_uniqueid:
            return context

        # Validate the uniqueid is numeric
        if not selected_uniqueid.isdigit():
            messages.error(self.request, 'Invalid polling unit selection.')
            return context

        try:
            polling_unit = PollingUnit.objects.get(uniqueid=int(selected_uniqueid))
        except PollingUnit.DoesNotExist:
            messages.error(self.request, 'The selected polling unit could not be found.')
            return context

        # Fetch results — polling_unit_uniqueid stores the uniqueid as a string
        results = (
            AnnouncedPuResults.objects
            .filter(polling_unit_uniqueid=selected_uniqueid)
            .order_by('-party_score')
        )

        if not results.exists():
            messages.info(
                self.request,
                f'No results have been entered for '
                f'{polling_unit.polling_unit_name} yet.'
            )
            context['selected_unit'] = polling_unit
            return context

        total_votes = results.aggregate(total=Sum('party_score'))['total'] or 0

        # Serialise chart data for Chart.js
        chart_labels = [r.party_abbreviation for r in results]
        chart_data = [r.party_score for r in results]

        context.update({
            'selected_unit': polling_unit,
            'results': results,
            'total_votes': total_votes,
            'winner': results.first(),
            'chart_labels': json.dumps(chart_labels),
            'chart_data': json.dumps(chart_data),
        })
        return context


class LgaResultsView(TemplateView):
    """
    Question 2 — Aggregated election results for an LGA.

    Votes are summed from announced_pu_results (NOT from announced_lga_results).

    Two-step ORM approach (required because polling_unit_uniqueid is a
    CharField, not a FK):
      Step 1: collect polling_unit.uniqueid integers for polling units in the LGA.
      Step 2: convert to strings, filter announced_pu_results, aggregate by party.
    """

    template_name = 'elections/lga_results.html'

    def get_context_data(self, **kwargs):
        """
        Build context for the LGA results page.

        Always provides the full Delta State LGA list for the dropdown.
        When an lga_id is supplied, aggregates polling unit results and
        serialises chart data as JSON.
        """
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'LGA Aggregated Results'

        # All Delta State LGAs for the dropdown
        context['lgas'] = (
            Lga.objects.filter(state_id=25).order_by('lga_name')
        )

        lga_id_param = self.request.GET.get('lga_id', '').strip()
        context['selected_lga_id'] = lga_id_param

        if not lga_id_param:
            return context

        if not lga_id_param.isdigit():
            messages.error(self.request, 'Invalid LGA selection.')
            return context

        lga_id = int(lga_id_param)

        try:
            lga = Lga.objects.get(lga_id=lga_id, state_id=25)
        except Lga.DoesNotExist:
            messages.error(self.request, 'The selected LGA could not be found.')
            return context

        # Step 1: collect integer uniqueid values for all polling units in this LGA
        unit_pk_ints = list(
            PollingUnit.objects
            .filter(lga_id=lga_id)
            .values_list('uniqueid', flat=True)
        )

        polling_unit_count = len(unit_pk_ints)

        if polling_unit_count == 0:
            messages.info(self.request, f'No polling units found for {lga.lga_name}.')
            context['selected_lga'] = lga
            return context

        # Step 2: convert to strings to match the varchar column, then aggregate
        unit_id_strs = [str(pk) for pk in unit_pk_ints]

        results = (
            AnnouncedPuResults.objects
            .filter(polling_unit_uniqueid__in=unit_id_strs)
            .values('party_abbreviation')
            .annotate(total_score=Sum('party_score'))
            .order_by('-total_score')
        )

        if not results.exists():
            messages.info(
                self.request,
                f'No announced results found for polling units in {lga.lga_name}.'
            )
            context['selected_lga'] = lga
            context['polling_unit_count'] = polling_unit_count
            return context

        total_votes = sum(r['total_score'] for r in results)

        # Serialise chart data for Chart.js
        chart_labels = [r['party_abbreviation'] for r in results]
        chart_data = [r['total_score'] for r in results]

        context.update({
            'selected_lga': lga,
            'results': results,
            'total_votes': total_votes,
            'polling_unit_count': polling_unit_count,
            'winner': results[0]['party_abbreviation'],
            'chart_labels': json.dumps(chart_labels),
            'chart_data': json.dumps(chart_data),
        })
        return context


class AddResultView(FormView):
    """
    Question 3 — Store election results for a new polling unit.

    Presents a dynamic form with one score field per party.  On valid
    submission, inserts one AnnouncedPuResults row per party inside a
    single database transaction.  On success, redirects to the polling
    unit results page so the user can immediately see the saved data.
    """

    template_name = 'elections/add_result.html'
    form_class = PollingUnitResultForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Add Polling Unit Results'
        # Count distinct parties so the live tally widget can display it.
        context['party_count'] = (
            AnnouncedPuResults.objects
            .values('party_abbreviation')
            .distinct()
            .count()
        )
        return context

    def form_valid(self, form):
        """
        Persist results for the selected polling unit.

        All AnnouncedPuResults rows are created inside transaction.atomic()
        so a failure midway through rolls back the entire batch.

        polling_unit_uniqueid is stored as str(polling_unit.uniqueid) to
        match the varchar column convention in announced_pu_results.
        The datetime column is date_entered (not time_of_entry).
        """
        polling_unit = form.cleaned_data['polling_unit']
        ip_address = self.request.META.get('REMOTE_ADDR', '127.0.0.1')
        entry_time = datetime.now()
        uniqueid_str = str(polling_unit.uniqueid)

        try:
            with transaction.atomic():
                for field_name, score in form.cleaned_data.items():
                    if not field_name.startswith('score_'):
                        continue
                    party = field_name[len('score_'):]
                    AnnouncedPuResults.objects.create(
                        polling_unit_uniqueid=uniqueid_str,
                        party_abbreviation=party,
                        party_score=score if score is not None else 0,
                        entered_by_user='admin',
                        user_ip_address=ip_address,
                        date_entered=entry_time,
                    )
        except Exception as exc:
            messages.error(
                self.request,
                f'An error occurred while saving results: {exc}'
            )
            return self.form_invalid(form)

        messages.success(
            self.request,
            f'Results successfully saved for {polling_unit.polling_unit_name}!'
        )

        redirect_url = (
            reverse('polling_unit')
            + f'?polling_unit_uniqueid={polling_unit.uniqueid}'
        )
        return redirect(redirect_url)

    def form_invalid(self, form):
        """Re-render the form with validation errors."""
        messages.error(
            self.request,
            'Please correct the errors below before submitting.'
        )
        return super().form_invalid(form)
