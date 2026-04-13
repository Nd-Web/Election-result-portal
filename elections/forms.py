"""
Forms for the elections app.

PollingUnitResultForm dynamically builds one IntegerField per party
by querying the distinct party abbreviations already present in the
announced_pu_results table.

Schema note: polling_unit has no state_id column.  Delta State units are
found by joining through the lga table (lga.state_id = 25, lga.lga_id =
polling_unit.lga_id).
"""

from django import forms

from .models import AnnouncedPuResults, Lga, PollingUnit

# Sanity cap — protects against obviously erroneous data entry only.
# Real polling units in the DB have totals well above 5,000, so this is
# set high enough never to reject genuine results.
MAX_TOTAL_VOTES = 500_000


def _delta_state_polling_units():
    """Return a queryset of all polling units in Delta State (state_id=25)."""
    delta_lga_ids = (
        Lga.objects.filter(state_id=25).values_list('lga_id', flat=True)
    )
    return (
        PollingUnit.objects
        .filter(lga_id__in=delta_lga_ids)
        .order_by('polling_unit_name')
    )


class PollingUnitResultForm(forms.Form):
    """
    Dynamic form for entering election results for a new polling unit.

    Fields are constructed at instantiation time:
    - polling_unit  : ModelChoiceField — Delta State polling units
    - score_<PARTY> : IntegerField    — one field per distinct party
    """

    polling_unit = forms.ModelChoiceField(
        queryset=PollingUnit.objects.none(),  # overridden in __init__
        label='Select Polling Unit',
        empty_label='-- Select a Polling Unit --',
        widget=forms.Select(attrs={'class': 'form-select form-select-lg'}),
    )

    def __init__(self, *args, **kwargs):
        """
        Set the correct polling unit queryset and dynamically append one
        score field per party abbreviation found in announced_pu_results.
        """
        super().__init__(*args, **kwargs)

        self.fields['polling_unit'].queryset = _delta_state_polling_units()

        parties = (
            AnnouncedPuResults.objects
            .values_list('party_abbreviation', flat=True)
            .distinct()
            .order_by('party_abbreviation')
        )

        for party in parties:
            field_name = f'score_{party}'
            self.fields[field_name] = forms.IntegerField(
                label=party,
                min_value=0,
                required=True,
                initial=0,
                widget=forms.NumberInput(
                    attrs={
                        'class': 'form-control',
                        'min': '0',
                        'placeholder': '0',
                    }
                ),
            )

    def clean(self):
        """
        Cross-field validation:
        1. The selected polling unit must not already have results.
        2. At least one party score must be greater than zero.
        3. The total of all scores must not exceed MAX_TOTAL_VOTES.
        """
        cleaned_data = super().clean()
        polling_unit = cleaned_data.get('polling_unit')

        if polling_unit:
            # Check for duplicate: compare against str(uniqueid)
            already_exists = AnnouncedPuResults.objects.filter(
                polling_unit_uniqueid=str(polling_unit.uniqueid)
            ).exists()
            if already_exists:
                raise forms.ValidationError(
                    f"Results for '{polling_unit.polling_unit_name}' have already "
                    "been entered. Each polling unit can only be submitted once."
                )

        total_votes = 0
        for field_name, value in cleaned_data.items():
            if field_name.startswith('score_') and value is not None:
                total_votes += value

        if total_votes == 0:
            raise forms.ValidationError(
                'At least one party must have a score greater than zero.'
            )

        if total_votes > MAX_TOTAL_VOTES:
            raise forms.ValidationError(
                f'Total votes ({total_votes:,}) exceeds the maximum allowed '
                f'({MAX_TOTAL_VOTES:,}) for a single polling unit. '
                'Please check your entries.'
            )

        return cleaned_data

    def get_party_fields(self):
        """
        Yield (field_name, bound_field) pairs for all party score fields.
        Used in the template to render score inputs in a grid layout.
        """
        for field_name in self.fields:
            if field_name.startswith('score_'):
                yield field_name, self[field_name]
