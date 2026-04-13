"""
Models for the elections app.

All models map to pre-existing tables in the bincom_test MySQL database.
managed = False on every model ensures Django never creates, alters, or
drops these tables.

Schema notes (verified against bincom_test.sql)
------------------------------------------------
* The `lga` table has `uniqueid` as its PK and `lga_id` as a *separate*
  integer field.  The same pattern applies to `ward`.

* `polling_unit` has no `state_id` column.  Filtering to Delta State must
  go through the lga table (lga.state_id = 25).

* `announced_pu_results.polling_unit_uniqueid` (varchar) stores the string
  representation of `polling_unit.uniqueid` (int PK).  It is NOT a FK
  and does NOT reference any `polling_unit_uniqueid` column (which does
  not exist in the actual table).

* The datetime column in both results tables is named `date_entered`,
  not `time_of_entry` as the brief suggested.

* `announced_lga_results` stores `lga_name` (varchar), not `lga_id` (int).

* The states table is named `states`, not `state_details`.
"""

from django.db import models


class StateDetails(models.Model):
    """Nigerian state master record.  Maps to the `states` table."""

    state_id = models.IntegerField(primary_key=True)
    state_name = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'states'

    def __str__(self) -> str:
        return self.state_name


class Lga(models.Model):
    """
    Local Government Area.

    NOTE: The PK is `uniqueid`, not `lga_id`.  The `lga_id` field is a
    separate logical identifier used by `polling_unit.lga_id`.
    """

    uniqueid = models.AutoField(primary_key=True)
    lga_id = models.IntegerField()
    lga_name = models.CharField(max_length=50)
    state_id = models.IntegerField()
    lga_description = models.TextField(blank=True, null=True)
    entered_by_user = models.CharField(max_length=50)
    date_entered = models.DateTimeField()
    user_ip_address = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'lga'

    def __str__(self) -> str:
        return self.lga_name


class Ward(models.Model):
    """
    Administrative ward within an LGA.

    NOTE: The PK is `uniqueid`, not `ward_id`.  The `ward_id` field is a
    separate logical identifier used by `polling_unit.ward_id`.
    """

    uniqueid = models.AutoField(primary_key=True)
    ward_id = models.IntegerField()
    ward_name = models.CharField(max_length=50)
    lga_id = models.IntegerField()
    ward_description = models.TextField(blank=True, null=True)
    entered_by_user = models.CharField(max_length=50)
    date_entered = models.DateTimeField()
    user_ip_address = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'ward'

    def __str__(self) -> str:
        return self.ward_name


class PollingUnit(models.Model):
    """
    Polling unit — the lowest level of the election hierarchy.

    IMPORTANT: This table has NO `state_id` and NO `polling_unit_uniqueid`
    column.  To filter to Delta State, join through Lga (lga.state_id=25).

    `announced_pu_results.polling_unit_uniqueid` stores str(polling_unit.uniqueid).
    """

    uniqueid = models.AutoField(primary_key=True)
    polling_unit_id = models.IntegerField()
    ward_id = models.IntegerField()
    lga_id = models.IntegerField()
    uniquewardid = models.IntegerField(blank=True, null=True)
    polling_unit_number = models.CharField(max_length=50, blank=True, null=True)
    polling_unit_name = models.CharField(max_length=50, blank=True, null=True)
    polling_unit_description = models.TextField(blank=True, null=True)
    lat = models.CharField(max_length=255, blank=True, null=True)
    long = models.CharField(max_length=255, blank=True, null=True)
    entered_by_user = models.CharField(max_length=50, blank=True, null=True)
    date_entered = models.DateTimeField(blank=True, null=True)
    user_ip_address = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'polling_unit'

    def __str__(self) -> str:
        return self.polling_unit_name or f'Polling Unit {self.uniqueid}'


class AnnouncedPuResults(models.Model):
    """
    Announced election result per party for a single polling unit.

    `polling_unit_uniqueid` is a CharField that stores str(polling_unit.uniqueid).
    The column in the DB is `date_entered` (not `time_of_entry`).
    """

    result_id = models.AutoField(primary_key=True)
    polling_unit_uniqueid = models.CharField(max_length=50)
    party_abbreviation = models.CharField(max_length=10)
    party_score = models.IntegerField()
    entered_by_user = models.CharField(max_length=50)
    date_entered = models.DateTimeField()
    user_ip_address = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'announced_pu_results'

    def __str__(self) -> str:
        return (
            f'{self.party_abbreviation}: {self.party_score} '
            f'(unit {self.polling_unit_uniqueid})'
        )


class AnnouncedLgaResults(models.Model):
    """
    Officially announced result per party for an LGA.

    NOTE: The link column is `lga_name` (varchar), not `lga_id` (int).
    The datetime column is `date_entered`, not `time_of_entry`.
    This table is NOT used in the aggregation view (Q2).
    """

    result_id = models.AutoField(primary_key=True)
    lga_name = models.CharField(max_length=50)
    party_abbreviation = models.CharField(max_length=10)
    party_score = models.IntegerField()
    entered_by_user = models.CharField(max_length=50)
    date_entered = models.DateTimeField()
    user_ip_address = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'announced_lga_results'

    def __str__(self) -> str:
        return f'{self.party_abbreviation}: {self.party_score} (LGA {self.lga_name})'
