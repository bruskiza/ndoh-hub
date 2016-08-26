import datetime
import json
import responses

from django.test import TestCase
from django.contrib.auth.models import User
from django.db.models.signals import post_save

from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from rest_hooks.models import model_saved

from ndoh_hub import utils, utils_tests
from .models import Change, psh_validate_implement
from .tasks import validate_implement
from registrations.models import (Source, Registration, SubscriptionRequest,
                                  psh_validate_subscribe)


def override_get_today():
    return datetime.datetime.strptime("20150817", "%Y%m%d")


def mock_get_active_subscriptions(registrant_id):
    subscription_id_1 = "subscription1-4bf1-8779-c47b428e89d0"
    subscription_id_2 = "subscription2-4bf1-8779-c47b428e89d0"
    responses.add(
        responses.GET,
        'http://sbm/api/v1/subscriptions/?active=True&id=%s' % registrant_id,
        json={
            "count": 2,
            "next": None,
            "previous": None,
            "results": [
                {   # pmtct_prebirth.patient.1 subscription
                    "id": subscription_id_1,
                    "identity": registrant_id,
                    "active": True,
                    "completed": False,
                    "lang": "eng_ZA",
                    "url": "http://sbm/api/v1/subscriptions/%s" % (
                        subscription_id_1),
                    "messageset": 11,
                    "next_sequence_number": 11,
                    "schedule": 101,
                    "process_status": 0,
                    "version": 1,
                    "metadata": {},
                    "created_at": "2015-07-10T06:13:29.693272Z",
                    "updated_at": "2015-07-10T06:13:29.693272Z"
                },
                {   # momconnect_prebirth.hw_full.1 subscription
                    "id": subscription_id_2,
                    "identity": registrant_id,
                    "active": True,
                    "completed": False,
                    "lang": "eng_ZA",
                    "url": "http://sbm/api/v1/subscriptions/%s" % (
                        subscription_id_2),
                    "messageset": 21,
                    "next_sequence_number": 21,
                    "schedule": 121,
                    "process_status": 0,
                    "version": 1,
                    "metadata": {},
                    "created_at": "2015-07-10T06:13:29.693272Z",
                    "updated_at": "2015-07-10T06:13:29.693272Z"
                }
            ],
        },
        status=200, content_type='application/json',
        match_querystring=True
    )

    return [subscription_id_1, subscription_id_2]


def mock_get_active_nurseconnect_subscriptions(registrant_id):
    subscription_id = "subscription1-4bf1-8779-c47b428e89d0"
    responses.add(
        responses.GET,
        'http://sbm/api/v1/subscriptions/?active=True&messageset=61&id=%s' % (
            registrant_id),
        json={
            "count": 1,
            "next": None,
            "previous": None,
            "results": [
                {   # nurseconnect.hw_full.1 subscription
                    "id": subscription_id,
                    "identity": registrant_id,
                    "active": True,
                    "completed": False,
                    "lang": "eng_ZA",
                    "url": "http://sbm/api/v1/subscriptions/%s" % (
                        subscription_id),
                    "messageset": 61,
                    "next_sequence_number": 11,
                    "schedule": 161,
                    "process_status": 0,
                    "version": 1,
                    "metadata": {},
                    "created_at": "2015-07-10T06:13:29.693272Z",
                    "updated_at": "2015-07-10T06:13:29.693272Z"
                }
            ]
        },
        status=200, content_type='application/json',
        match_querystring=True
    )

    return [subscription_id]


def mock_deactivate_subscriptions(subscription_ids):
    for subscription_id in subscription_ids:
        responses.add(
            responses.PATCH,
            'http://sbm/api/v1/subscriptions/%s/' % subscription_id,
            json={"active": False},
            status=200, content_type='application/json',
        )
    return


class APITestCase(TestCase):

    def setUp(self):
        self.adminclient = APIClient()
        self.normalclient = APIClient()
        self.otherclient = APIClient()
        utils.get_today = override_get_today


class AuthenticatedAPITestCase(APITestCase):

    def _replace_post_save_hooks_change(self):
        def has_listeners():
            return post_save.has_listeners(Change)
        assert has_listeners(), (
            "Change model has no post_save listeners. Make sure"
            " helpers cleaned up properly in earlier tests.")
        post_save.disconnect(receiver=psh_validate_implement,
                             sender=Change)
        post_save.disconnect(receiver=model_saved,
                             dispatch_uid='instance-saved-hook')
        assert not has_listeners(), (
            "Change model still has post_save listeners. Make sure"
            " helpers cleaned up properly in earlier tests.")

    def _restore_post_save_hooks_change(self):
        def has_listeners():
            return post_save.has_listeners(Change)
        assert not has_listeners(), (
            "Change model still has post_save listeners. Make sure"
            " helpers removed them properly in earlier tests.")
        post_save.connect(psh_validate_implement, sender=Change)

    def _replace_post_save_hooks_registration(self):
        def has_listeners():
            return post_save.has_listeners(Registration)
        assert has_listeners(), (
            "Registration model has no post_save listeners. Make sure"
            " helpers cleaned up properly in earlier tests.")
        post_save.disconnect(receiver=psh_validate_subscribe,
                             sender=Registration)
        post_save.disconnect(receiver=model_saved,
                             dispatch_uid='instance-saved-hook')
        assert not has_listeners(), (
            "Registration model still has post_save listeners. Make sure"
            " helpers cleaned up properly in earlier tests.")

    def _restore_post_save_hooks_registration(self):
        def has_listeners():
            return post_save.has_listeners(Registration)
        assert not has_listeners(), (
            "Registration model still has post_save listeners. Make sure"
            " helpers removed them properly in earlier tests.")
        post_save.connect(psh_validate_subscribe, sender=Registration)

    def make_source_adminuser(self):
        data = {
            "name": "test_source_adminuser",
            "authority": "hw_full",
            "user": User.objects.get(username='testadminuser')
        }
        return Source.objects.create(**data)

    def make_source_normaluser(self):
        data = {
            "name": "test_source_normaluser",
            "authority": "patient",
            "user": User.objects.get(username='testnormaluser')
        }
        return Source.objects.create(**data)

    def make_change_adminuser(self):
        data = {
            "registrant_id": "mother01-63e2-4acc-9b94-26663b9bc267",
            "action": "pmtct_loss_switch",
            "data": {"test_adminuser_change": "test_adminuser_changed"},
            "source": self.make_source_adminuser()
        }
        return Change.objects.create(**data)

    def make_change_normaluser(self):
        data = {
            "registrant_id": "mother01-63e2-4acc-9b94-26663b9bc267",
            "action": "pmtct_loss_switch",
            "data": {"test_normaluser_change": "test_normaluser_changed"},
            "source": self.make_source_normaluser()
        }
        return Change.objects.create(**data)

    def make_registration_pmtct_prebirth(self):
        registration_data = {
            "reg_type": "pmtct_prebirth",
            "registrant_id": "mother01-63e2-4acc-9b94-26663b9bc267",
            "source": self.make_source_normaluser(),
            "data": {
                "operator_id": "mother01-63e2-4acc-9b94-26663b9bc267",
                "language": "eng_ZA",
                "mom_dob": "1999-01-27",
                "edd": "2016-11-30",
            },
        }
        return Registration.objects.create(**registration_data)

    def make_registration_pmtct_postbirth(self):
        registration_data = {
            "reg_type": "pmtct_postbirth",
            "registrant_id": "mother01-63e2-4acc-9b94-26663b9bc267",
            "source": self.make_source_normaluser(),
            "data": {
                "operator_id": "mother01-63e2-4acc-9b94-26663b9bc267",
                "language": "eng_ZA",
                "mom_dob": "1999-01-27",
                "baby_dob": "2016-01-01"
            },
        }
        return Registration.objects.create(**registration_data)

    def make_registration_nurseconnect(self):
        registration_data = {
            "reg_type": "nurseconnect",
            "registrant_id": "nurse001-63e2-4acc-9b94-26663b9bc267",
            "source": self.make_source_adminuser(),
            "data": {
                "operator_id": "mother01-63e2-4acc-9b94-26663b9bc267",
                "msisdn_registrant": "+27821112222",
                "msisdn_device": "+27821112222",
                "faccode": "123456",
            },
        }
        return Registration.objects.create(**registration_data)

    def setUp(self):
        super(AuthenticatedAPITestCase, self).setUp()
        self._replace_post_save_hooks_change()
        self._replace_post_save_hooks_registration()

        # Normal User setup
        self.normalusername = 'testnormaluser'
        self.normalpassword = 'testnormalpass'
        self.normaluser = User.objects.create_user(
            self.normalusername,
            'testnormaluser@example.com',
            self.normalpassword)
        normaltoken = Token.objects.create(user=self.normaluser)
        self.normaltoken = normaltoken.key
        self.normalclient.credentials(
            HTTP_AUTHORIZATION='Token ' + self.normaltoken)

        # Admin User setup
        self.adminusername = 'testadminuser'
        self.adminpassword = 'testadminpass'
        self.adminuser = User.objects.create_superuser(
            self.adminusername,
            'testadminuser@example.com',
            self.adminpassword)
        admintoken = Token.objects.create(user=self.adminuser)
        self.admintoken = admintoken.key
        self.adminclient.credentials(
            HTTP_AUTHORIZATION='Token ' + self.admintoken)

    def tearDown(self):
        self._restore_post_save_hooks_change()
        self._restore_post_save_hooks_registration()


class TestChangeAPI(AuthenticatedAPITestCase):

    def test_get_change_adminuser(self):
        # Setup
        change = self.make_change_adminuser()
        # Execute
        response = self.adminclient.get(
            '/api/v1/change/%s/' % change.id,
            content_type='application/json')
        # Check
        # Currently only posts are allowed
        self.assertEqual(response.status_code,
                         status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_get_change_normaluser(self):
        # Setup
        change = self.make_change_normaluser()
        # Execute
        response = self.normalclient.get(
            '/api/v1/change/%s/' % change.id,
            content_type='application/json')
        # Check
        # Currently only posts are allowed
        self.assertEqual(response.status_code,
                         status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_create_change_adminuser(self):
        # Setup
        self.make_source_adminuser()
        post_data = {
            "registrant_id": "846877e6-afaa-43de-acb1-09f61ad4de99",
            "action": "pmtct_loss_switch",
            "data": {"test_key1": "test_value1"}
        }
        # Execute
        response = self.adminclient.post('/api/v1/change/',
                                         json.dumps(post_data),
                                         content_type='application/json')
        # Check
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        d = Change.objects.last()
        self.assertEqual(d.source.name, 'test_source_adminuser')
        self.assertEqual(d.action, 'pmtct_loss_switch')
        self.assertEqual(d.validated, False)
        self.assertEqual(d.data, {"test_key1": "test_value1"})
        self.assertEqual(d.created_by, self.adminuser)

    def test_create_change_normaluser(self):
        # Setup
        self.make_source_normaluser()
        post_data = {
            "registrant_id": "846877e6-afaa-43de-acb1-09f61ad4de99",
            "action": "pmtct_loss_switch",
            "data": {"test_key1": "test_value1"}
        }
        # Execute
        response = self.normalclient.post('/api/v1/change/',
                                          json.dumps(post_data),
                                          content_type='application/json')
        # Check
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        d = Change.objects.last()
        self.assertEqual(d.source.name, 'test_source_normaluser')
        self.assertEqual(d.action, 'pmtct_loss_switch')
        self.assertEqual(d.validated, False)
        self.assertEqual(d.data, {"test_key1": "test_value1"})
        self.assertEqual(d.created_by, self.normaluser)

    def test_create_change_set_readonly_field(self):
        # Setup
        self.make_source_adminuser()
        post_data = {
            "registrant_id": "846877e6-afaa-43de-acb1-09f61ad4de99",
            "action": "pmtct_loss_switch",
            "data": {"test_key1": "test_value1"},
            "validated": True
        }
        # Execute
        response = self.adminclient.post('/api/v1/change/',
                                         json.dumps(post_data),
                                         content_type='application/json')
        # Check
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        d = Change.objects.last()
        self.assertEqual(d.source.name, 'test_source_adminuser')
        self.assertEqual(d.action, 'pmtct_loss_switch')
        self.assertEqual(d.validated, False)  # Should ignore True post_data
        self.assertEqual(d.data, {"test_key1": "test_value1"})


class TestRegistrationCreation(AuthenticatedAPITestCase):

    def test_make_registration_pmtct_prebirth(self):
        # Setup
        # Execute
        self.make_registration_pmtct_prebirth()
        # Test
        d = Registration.objects.last()
        self.assertEqual(d.registrant_id,
                         "mother01-63e2-4acc-9b94-26663b9bc267")
        self.assertEqual(d.data["mom_dob"], "1999-01-27")


class TestChangeValidation(AuthenticatedAPITestCase):

    def test_validate_baby_switch_good(self):
        """ Good data baby_switch test """
        # Setup
        change_data = {
            "registrant_id": "mother01-63e2-4acc-9b94-26663b9bc267",
            "action": "baby_switch",
            "data": {},
            "source": self.make_source_normaluser()
        }
        change = Change.objects.create(**change_data)
        # Execute
        c = validate_implement.validate(change)
        # Check
        change.refresh_from_db()
        self.assertEqual(c, True)
        self.assertEqual(change.validated, True)

    def test_validate_baby_switch_malformed_data(self):
        """ Malformed data baby_switch test """
        # Setup
        change_data = {
            "registrant_id": "mother01",
            "action": "baby_switch",
            "data": {},
            "source": self.make_source_normaluser()
        }
        change = Change.objects.create(**change_data)
        # Execute
        c = validate_implement.validate(change)
        # Check
        change.refresh_from_db()
        self.assertEqual(c, False)
        self.assertEqual(change.validated, False)
        self.assertEqual(change.data["invalid_fields"], [
            'Invalid UUID registrant_id']
        )

    def test_validate_pmtct_loss_optouts_good(self):
        """ Loss optout data blobs are essentially identical between different
        forms of loss optout for pmtct, so just test one good one.
        """
        # Setup
        change_data = {
            "registrant_id": "mother01-63e2-4acc-9b94-26663b9bc267",
            "action": "pmtct_loss_switch",
            "data": {
                "reason": "miscarriage"
            },
            "source": self.make_source_normaluser()
        }
        change = Change.objects.create(**change_data)
        # Execute
        c = validate_implement.validate(change)
        # Check
        change.refresh_from_db()
        self.assertEqual(c, True)
        self.assertEqual(change.validated, True)

    def test_validate_pmtct_loss_optouts_malformed_data(self):
        """ Loss optout data blobs are essentially identical between different
        forms of loss optout for pmtct, so just test one malformed one.
        """
        # Setup
        change_data = {
            "registrant_id": "mother01",
            "action": "pmtct_loss_switch",
            "data": {
                "reason": "not a reason we accept"
            },
            "source": self.make_source_normaluser()
        }
        change = Change.objects.create(**change_data)
        # Execute
        c = validate_implement.validate(change)
        # Check
        change.refresh_from_db()
        self.assertEqual(c, False)
        self.assertEqual(change.validated, False)
        self.assertEqual(change.data["invalid_fields"], [
            'Invalid UUID registrant_id', 'Not a valid loss reason']
        )

    def test_validate_pmtct_loss_optouts_missing_data(self):
        """ Loss optout data blobs are essentially identical between different
        forms of loss optout for pmtct, so just test one missing one.
        """
        # Setup
        change_data = {
            "registrant_id": "mother01-63e2-4acc-9b94-26663b9bc267",
            "action": "pmtct_loss_switch",
            "data": {},
            "source": self.make_source_normaluser()
        }
        change = Change.objects.create(**change_data)
        # Execute
        c = validate_implement.validate(change)
        # Check
        change.refresh_from_db()
        self.assertEqual(c, False)
        self.assertEqual(change.validated, False)
        self.assertEqual(change.data["invalid_fields"], [
            'Optout reason is missing']
        )

    def test_validate_pmtct_nonloss_optouts_good(self):
        """ Good data nonloss optout """
        # Setup
        change_data = {
            "registrant_id": "mother01-63e2-4acc-9b94-26663b9bc267",
            "action": "pmtct_nonloss_optout",
            "data": {
                "reason": "not_hiv_pos"
            },
            "source": self.make_source_normaluser()
        }
        change = Change.objects.create(**change_data)
        # Execute
        c = validate_implement.validate(change)
        # Check
        change.refresh_from_db()
        self.assertEqual(c, True)
        self.assertEqual(change.validated, True)

    def test_validate_pmtct_nonloss_optouts_malformed_data(self):
        """ Loss optout data blobs are essentially identical between different
        forms of loss optout for pmtct, so just test one malformed one.
        """
        # Setup
        change_data = {
            "registrant_id": "mother01",
            "action": "pmtct_nonloss_optout",
            "data": {
                "reason": "miscarriage"
            },
            "source": self.make_source_normaluser()
        }
        change = Change.objects.create(**change_data)
        # Execute
        c = validate_implement.validate(change)
        # Check
        change.refresh_from_db()
        self.assertEqual(c, False)
        self.assertEqual(change.validated, False)
        self.assertEqual(change.data["invalid_fields"], [
            'Invalid UUID registrant_id', 'Not a valid nonloss reason']
        )

    def test_validate_pmtct_nonloss_optouts_missing_data(self):
        """ Loss optout data blobs are essentially identical between different
        forms of loss optout for pmtct, so just test one missing one.
        """
        # Setup
        change_data = {
            "registrant_id": "mother01-63e2-4acc-9b94-26663b9bc267",
            "action": "pmtct_loss_switch",
            "data": {},
            "source": self.make_source_normaluser()
        }
        change = Change.objects.create(**change_data)
        # Execute
        c = validate_implement.validate(change)
        # Check
        change.refresh_from_db()
        self.assertEqual(c, False)
        self.assertEqual(change.validated, False)
        self.assertEqual(change.data["invalid_fields"], [
            'Optout reason is missing']
        )

    def test_validate_nurse_update_faccode_good(self):
        """ Good data faccode update """
        # Setup
        change_data = {
            "registrant_id": "nurse001-63e2-4acc-9b94-26663b9bc267",
            "action": "nurse_update_detail",
            "data": {
                "faccode": "234567"
            },
            "source": self.make_source_adminuser()
        }
        change = Change.objects.create(**change_data)
        # Execute
        c = validate_implement.validate(change)
        # Check
        change.refresh_from_db()
        self.assertEqual(c, True)
        self.assertEqual(change.validated, True)

    def test_validate_nurse_update_faccode_and_sanc(self):
        # Setup
        change_data = {
            "registrant_id": "nurse001-63e2-4acc-9b94-26663b9bc267",
            "action": "nurse_update_detail",
            "data": {
                "faccode": "234567",
                "sanc_no": "1234"
            },
            "source": self.make_source_adminuser()
        }
        change = Change.objects.create(**change_data)
        # Execute
        c = validate_implement.validate(change)
        # Check
        change.refresh_from_db()
        self.assertEqual(c, False)
        self.assertEqual(change.validated, False)
        self.assertEqual(change.data["invalid_fields"], [
            'Only one detail update can be submitted per Change'])

    def test_validate_nurse_update_faccode_malformed(self):
        # Setup
        change_data = {
            "registrant_id": "nurse001",
            "action": "nurse_update_detail",
            "data": {
                "faccode": "",
            },
            "source": self.make_source_adminuser()
        }
        change = Change.objects.create(**change_data)
        # Execute
        c = validate_implement.validate(change)
        # Check
        change.refresh_from_db()
        self.assertEqual(c, False)
        self.assertEqual(change.validated, False)
        self.assertEqual(change.data["invalid_fields"], [
            'Invalid UUID registrant_id', 'Faccode invalid'])

    # skip sanc_no and persal_no update tests - similar to faccode update

    def test_validate_nurse_update_sa_id_good(self):
        # Setup
        change_data = {
            "registrant_id": "nurse001-63e2-4acc-9b94-26663b9bc267",
            "action": "nurse_update_detail",
            "data": {
                "id_type": "sa_id",
                "sa_id_no": "5101025009086",
                "dob": "1951-01-02"
            },
            "source": self.make_source_adminuser()
        }
        change = Change.objects.create(**change_data)
        # Execute
        c = validate_implement.validate(change)
        # Check
        change.refresh_from_db()
        self.assertEqual(c, True)
        self.assertEqual(change.validated, True)

    def test_validate_nurse_update_id_type_invalid(self):
        # Setup
        change_data = {
            "registrant_id": "nurse001-63e2-4acc-9b94-26663b9bc267",
            "action": "nurse_update_detail",
            "data": {
                "id_type": "dob",
                "dob": "1951-01-02"
            },
            "source": self.make_source_adminuser()
        }
        change = Change.objects.create(**change_data)
        # Execute
        c = validate_implement.validate(change)
        # Check
        change.refresh_from_db()
        self.assertEqual(c, False)
        self.assertEqual(change.validated, False)
        self.assertEqual(change.data["invalid_fields"], [
            'ID type should be passport or sa_id'])

    def test_validate_nurse_update_sa_id_field_wrong(self):
        # Setup
        change_data = {
            "registrant_id": "nurse001-63e2-4acc-9b94-26663b9bc267",
            "action": "nurse_update_detail",
            "data": {
                "id_type": "sa_id",
                "passport_no": "12345",
                "dob": "1951-01-02"
            },
            "source": self.make_source_adminuser()
        }
        change = Change.objects.create(**change_data)
        # Execute
        c = validate_implement.validate(change)
        # Check
        change.refresh_from_db()
        self.assertEqual(c, False)
        self.assertEqual(change.validated, False)
        self.assertEqual(change.data["invalid_fields"], [
            'SA ID update requires fields id_type, sa_id_no, dob'])

    def test_validate_nurse_update_passport_good(self):
        # Setup
        change_data = {
            "registrant_id": "nurse001-63e2-4acc-9b94-26663b9bc267",
            "action": "nurse_update_detail",
            "data": {
                "id_type": "passport",
                "passport_no": "12345",
                "passport_origin": "na",
                "dob": "1951-01-02"
            },
            "source": self.make_source_adminuser()
        }
        change = Change.objects.create(**change_data)
        # Execute
        c = validate_implement.validate(change)
        # Check
        change.refresh_from_db()
        self.assertEqual(c, True)
        self.assertEqual(change.validated, True)

    def test_validate_nurse_update_passport_field_missing(self):
        # Setup
        change_data = {
            "registrant_id": "nurse001-63e2-4acc-9b94-26663b9bc267",
            "action": "nurse_update_detail",
            "data": {
                "id_type": "passport",
                "passport_no": "12345",
                "passport_origin": "na"
            },
            "source": self.make_source_adminuser()
        }
        change = Change.objects.create(**change_data)
        # Execute
        c = validate_implement.validate(change)
        # Check
        change.refresh_from_db()
        self.assertEqual(c, False)
        self.assertEqual(change.validated, False)
        self.assertEqual(change.data["invalid_fields"], [
            'Passport update requires fields id_type, passport_no, '
            'passport_origin, dob'])

    def test_validate_nurse_update_arbitrary(self):
        # Setup
        change_data = {
            "registrant_id": "nurse001-63e2-4acc-9b94-26663b9bc267",
            "action": "nurse_update_detail",
            "data": {
                "foo": "bar"
            },
            "source": self.make_source_adminuser()
        }
        change = Change.objects.create(**change_data)
        # Execute
        c = validate_implement.validate(change)
        # Check
        change.refresh_from_db()
        self.assertEqual(c, False)
        self.assertEqual(change.validated, False)
        self.assertEqual(change.data["invalid_fields"], [
            'Could not parse detail update request'])

    def test_validate_nurse_change_msisdn_good(self):
        # Setup
        change_data = {
            "registrant_id": "nurse001-63e2-4acc-9b94-26663b9bc267",
            "action": "nurse_change_msisdn",
            "data": {
                "msisdn_old": "+27820001001",
                "msisdn_new": "+27820001002",
                "msisdn_device": "+27820001001",
            },
            "source": self.make_source_adminuser()
        }
        change = Change.objects.create(**change_data)
        # Execute
        c = validate_implement.validate(change)
        # Check
        change.refresh_from_db()
        self.assertEqual(c, True)
        self.assertEqual(change.validated, True)

    def test_validate_nurse_change_msisdn_malformed(self):
        # Setup
        change_data = {
            "registrant_id": "nurse001-63e2-4acc-9b94-26663b9bc267",
            "action": "nurse_change_msisdn",
            "data": {
                "msisdn_old": "+27820001001",
                "msisdn_new": "+27820001002",
                "msisdn_device": "+27820001003",
            },
            "source": self.make_source_adminuser()
        }
        change = Change.objects.create(**change_data)
        # Execute
        c = validate_implement.validate(change)
        # Check
        change.refresh_from_db()
        self.assertEqual(c, False)
        self.assertEqual(change.validated, False)
        self.assertEqual(change.data["invalid_fields"], [
            'Device msisdn should be the same as new or old msisdn'])

    def test_validate_nurse_optout_good(self):
        """ Good data nonloss optout """
        # Setup
        change_data = {
            "registrant_id": "mother01-63e2-4acc-9b94-26663b9bc267",
            "action": "nurse_optout",
            "data": {
                "reason": "job_change"
            },
            "source": self.make_source_adminuser()
        }
        change = Change.objects.create(**change_data)
        # Execute
        c = validate_implement.validate(change)
        # Check
        change.refresh_from_db()
        self.assertEqual(c, True)
        self.assertEqual(change.validated, True)

    def test_validate_nurse_optout_malformed_data(self):
        """ Loss optout data blobs are essentially identical between different
        forms of loss optout for pmtct, so just test one malformed one.
        """
        # Setup
        change_data = {
            "registrant_id": "mother01",
            "action": "nurse_optout",
            "data": {
                "reason": "bored"
            },
            "source": self.make_source_adminuser()
        }
        change = Change.objects.create(**change_data)
        # Execute
        c = validate_implement.validate(change)
        # Check
        change.refresh_from_db()
        self.assertEqual(c, False)
        self.assertEqual(change.validated, False)
        self.assertEqual(change.data["invalid_fields"], [
            'Invalid UUID registrant_id', 'Not a valid optout reason']
        )


class TestChangeActions(AuthenticatedAPITestCase):

    @responses.activate
    def test_baby_switch_with_active_pmtct_subscription(self):
        # Pretest
        self.assertEqual(Registration.objects.all().count(), 0)
        # Setup
        # make registration
        self.make_registration_pmtct_prebirth()
        self.assertEqual(Registration.objects.all().count(), 1)
        self.assertEqual(SubscriptionRequest.objects.all().count(), 0)
        # make change object
        change_data = {
            "registrant_id": "mother01-63e2-4acc-9b94-26663b9bc267",
            "action": "baby_switch",
            "data": {},
            "source": self.make_source_normaluser()
        }
        change = Change.objects.create(**change_data)

        # . mock get subscription request
        active_subscription_ids = mock_get_active_subscriptions(
            change_data["registrant_id"])

        # . mock get messageset by id
        utils_tests.mock_get_messageset(11)
        utils_tests.mock_get_messageset(21)

        # . mock deactivate active subscriptions
        mock_deactivate_subscriptions(active_subscription_ids)

        # . mock get messageset by shortname
        schedule_id = utils_tests.mock_get_messageset_by_shortname(
            "pmtct_postbirth.patient.1")
        utils_tests.mock_get_schedule(schedule_id)

        # Execute
        result = validate_implement.apply_async(args=[change.id])

        # Check
        change.refresh_from_db()
        self.assertEqual(result.get(), True)
        self.assertEqual(change.validated, True)
        self.assertEqual(Registration.objects.all().count(), 1)
        self.assertEqual(SubscriptionRequest.objects.all().count(), 1)

    @responses.activate
    def test_pmtct_loss_switch(self):
        # Setup
        # make registration
        self.make_registration_pmtct_prebirth()
        self.assertEqual(Registration.objects.all().count(), 1)
        self.assertEqual(SubscriptionRequest.objects.all().count(), 0)
        # make change object
        change_data = {
            "registrant_id": "mother01-63e2-4acc-9b94-26663b9bc267",
            "action": "pmtct_loss_switch",
            "data": {
                "reason": "miscarriage"
            },
            "source": self.make_source_normaluser()
        }
        change = Change.objects.create(**change_data)

        # . mock get subscription request
        active_subscription_ids = mock_get_active_subscriptions(
            change_data["registrant_id"])

        # . mock deactivate active subscriptions
        mock_deactivate_subscriptions(active_subscription_ids)

        # Execute
        result = validate_implement.apply_async(args=[change.id])

        # Check
        change.refresh_from_db()
        self.assertEqual(result.get(), True)
        self.assertEqual(change.validated, True)
        self.assertEqual(Registration.objects.all().count(), 1)
        self.assertEqual(SubscriptionRequest.objects.all().count(), 0)

    @responses.activate
    def test_pmtct_loss_optout(self):
        # Setup
        # make registration
        self.make_registration_pmtct_prebirth()
        self.assertEqual(Registration.objects.all().count(), 1)
        self.assertEqual(SubscriptionRequest.objects.all().count(), 0)
        # make change object
        change_data = {
            "registrant_id": "mother01-63e2-4acc-9b94-26663b9bc267",
            "action": "pmtct_loss_optout",
            "data": {
                "reason": "stillbirth"
            },
            "source": self.make_source_normaluser()
        }
        change = Change.objects.create(**change_data)

        # . mock get subscription request
        active_subscription_ids = mock_get_active_subscriptions(
            change_data["registrant_id"])

        # . mock deactivate active subscriptions
        mock_deactivate_subscriptions(active_subscription_ids)

        # Execute
        result = validate_implement.apply_async(args=[change.id])

        # Check
        change.refresh_from_db()
        self.assertEqual(result.get(), True)
        self.assertEqual(change.validated, True)
        self.assertEqual(Registration.objects.all().count(), 1)
        self.assertEqual(SubscriptionRequest.objects.all().count(), 0)

    @responses.activate
    def test_pmtct_nonloss_optout(self):
        # Setup
        # make registration
        self.make_registration_pmtct_prebirth()
        self.assertEqual(Registration.objects.all().count(), 1)
        self.assertEqual(SubscriptionRequest.objects.all().count(), 0)
        # make change object
        change_data = {
            "registrant_id": "mother01-63e2-4acc-9b94-26663b9bc267",
            "action": "pmtct_nonloss_optout",
            "data": {
                "reason": "other"
            },
            "source": self.make_source_normaluser()
        }
        change = Change.objects.create(**change_data)

        # . mock get subscription request
        active_subscription_ids = mock_get_active_subscriptions(
            change_data["registrant_id"])

        # . mock deactivate active subscriptions
        mock_deactivate_subscriptions(active_subscription_ids)

        # Execute
        result = validate_implement.apply_async(args=[change.id])

        # Check
        change.refresh_from_db()
        self.assertEqual(result.get(), True)
        self.assertEqual(change.validated, True)
        self.assertEqual(Registration.objects.all().count(), 1)
        self.assertEqual(SubscriptionRequest.objects.all().count(), 0)

    @responses.activate
    def test_nurse_update_detail(self):
        # Setup
        # make registration
        self.make_registration_nurseconnect()
        self.assertEqual(Registration.objects.all().count(), 1)
        self.assertEqual(SubscriptionRequest.objects.all().count(), 0)
        # make change object
        change_data = {
            "registrant_id": "nurse001-63e2-4acc-9b94-26663b9bc267",
            "action": "nurse_update_detail",
            "data": {
                "faccode": "234567"
            },
            "source": self.make_source_adminuser()
        }
        change = Change.objects.create(**change_data)

        # Execute
        result = validate_implement.apply_async(args=[change.id])

        # Check
        change.refresh_from_db()
        self.assertEqual(result.get(), True)
        self.assertEqual(Registration.objects.all().count(), 1)
        self.assertEqual(SubscriptionRequest.objects.all().count(), 0)

    @responses.activate
    def test_nurse_change_msisdn(self):
        # Setup
        # make registration
        self.make_registration_nurseconnect()
        self.assertEqual(Registration.objects.all().count(), 1)
        self.assertEqual(SubscriptionRequest.objects.all().count(), 0)
        # make change object
        change_data = {
            "registrant_id": "nurse001-63e2-4acc-9b94-26663b9bc267",
            "action": "nurse_change_msisdn",
            "data": {
                "msisdn_old": "+27821112222",
                "msisdn_new": "+27821113333",
                "msisdn_device": "+27821113333",
            },
            "source": self.make_source_adminuser()
        }
        change = Change.objects.create(**change_data)

        # Execute
        result = validate_implement.apply_async(args=[change.id])

        # Check
        change.refresh_from_db()
        self.assertEqual(result.get(), True)
        self.assertEqual(change.validated, True)
        self.assertEqual(Registration.objects.all().count(), 1)
        self.assertEqual(SubscriptionRequest.objects.all().count(), 0)

    @responses.activate
    def test_nurse_optout(self):
        # Setup
        # make registration
        self.make_registration_nurseconnect()
        self.assertEqual(Registration.objects.all().count(), 1)
        self.assertEqual(SubscriptionRequest.objects.all().count(), 0)
        # make change object
        change_data = {
            "registrant_id": "nurse001-63e2-4acc-9b94-26663b9bc267",
            "action": "nurse_optout",
            "data": {
                "reason": "job_change"
            },
            "source": self.make_source_adminuser()
        }
        change = Change.objects.create(**change_data)

        # mock get messageset by shortname
        utils_tests.mock_get_messageset_by_shortname("nurseconnect.hw_full.1")

        # . mock get nurseconnect subscription request
        active_subscription_ids = mock_get_active_nurseconnect_subscriptions(
            change_data["registrant_id"])

        # . mock deactivate active subscriptions
        mock_deactivate_subscriptions(active_subscription_ids)

        # Execute
        result = validate_implement.apply_async(args=[change.id])

        # Check
        change.refresh_from_db()
        self.assertEqual(result.get(), True)
        self.assertEqual(change.validated, True)
        self.assertEqual(Registration.objects.all().count(), 1)
        self.assertEqual(SubscriptionRequest.objects.all().count(), 0)