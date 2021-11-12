# -*- encoding: utf-8 -*-
"""
KERI
keri.vdr.eventing module

VC TEL  support
"""

import json
import logging

from hio.help import decking
from math import ceil
from orderedset import OrderedSet as oset

from keri import kering
from keri.core import coring
from .. import core
from .. import help
from ..core.coring import (MtrDex, Serder, Serials, Versify, Prefixer,
                           Ilks, Seqner, Verfer)
from ..core.eventing import SealEvent, ample, TraitDex, verifySigs, validateSN
from ..db import basing, dbing
from ..db.dbing import dgKey, snKey
from ..help import helping
from ..kering import (MissingWitnessSignatureError, Version,
                      MissingAnchorError, ValidationError, OutOfOrderError, LikelyDuplicitousError)
from ..vdr.viring import Registry, nsKey

logger = help.ogler.getLogger()

VCP_LABELS = ["v", "i", "s", "t", "bt", "b", "c"]
VRT_LABELS = ["v", "i", "s", "t", "p", "bt", "b", "ba", "br"]

ISS_LABELS = ["v", "i", "s", "t", "ri", "dt"]
BIS_LABELS = ["v", "i", "s", "t", "ra", "dt"]

REV_LABELS = ["v", "i", "s", "t", "p", "dt"]
BRV_LABELS = ["v", "i", "s", "t", "ra", "p", "dt"]

TSN_LABELS = ["v", "i", "s", "t", "d", "ii", "a", "et", "bt", "b", "c", "br", "ba"]


def incept(
        pre,
        toad=None,
        baks=None,
        cnfg=None,
        version=Version,
        kind=Serials.json,
        code=None,
):
    """ Returns serder of credential registry inception (vcp) message event

    Returns serder of vcp message event
    Utility function to create a Registry inception event

    Parameters:
         pre (str): issuer identifier prefix qb64
         toad (int): int or str hex of backer threshold
         baks (list): the initial list of backers prefixes for VCs in the Registry
         cnfg (list): is list of strings TraitDex of configuration traits

         version (Versionage): the API version
         kind (str): the event type
         code (str): default code for Prefixer

    Returns:
        Serder: Event message Serder

    Todo:
        Apply nonce to registry inception event to guarantee uniquiness of identifier

    """

    vs = Versify(version=version, kind=kind, size=0)
    isn = 0
    ilk = Ilks.vcp

    cnfg = cnfg if cnfg is not None else []

    baks = baks if baks is not None else []
    if TraitDex.NoBackers in cnfg and len(baks) > 0:
        raise ValueError("{} backers specified for NB vcp, 0 allowed".format(len(baks)))

    if len(oset(baks)) != len(baks):
        raise ValueError("Invalid baks = {}, has duplicates.".format(baks))

    if isinstance(toad, str):
        toad = "{:x}".format(toad)
    elif toad is None:
        if not baks:
            toad = 0
        else:  # compute default f and m for len(baks)
            toad = ample(len(baks))

    if baks:
        if toad < 1 or toad > len(baks):  # out of bounds toad
            raise ValueError("Invalid toad = {} for baks = {}".format(toad, baks))
    else:
        if toad != 0:  # invalid toad
            raise ValueError("Invalid toad = {} for baks = {}".format(toad, baks))

    # preseed = pysodium.randombytes(pysodium.crypto_sign_SEEDBYTES)
    # seedqb64 = coring.Matter(raw=preseed, code=MtrDex.Ed25519_Seed).qb64

    ked = dict(v=vs,  # version string
               i="",  # qb64 prefix
               ii=pre,
               s="{:x}".format(isn),  # hex string no leading zeros lowercase
               t=ilk,
               c=cnfg,
               bt="{:x}".format(toad),  # hex string no leading zeros lowercase
               b=baks,  # list of qb64 may be empty
               # n=seedqb64  # nonce of random bytes to make each registry unique
               )

    prefixer = Prefixer(ked=ked, code=code, allows=[MtrDex.Blake3_256])  # Derive AID from ked and code
    ked["i"] = prefixer.qb64  # update pre element in ked with pre qb64

    return Serder(ked=ked)  # return serialized ked


def rotate(
        regk,
        dig,
        sn=1,
        toad=None,
        baks=None,
        cuts=None,
        adds=None,
        version=Version,
        kind=Serials.json,
):
    """ Returns serder of registry rotation (brt) message event

    Returns serder of vrt message event
    Utility function to create a Registry rotation event

    Parameters:
        regk (str): identifier prefix qb64
        dig (str): qb64 digest or prior event
        sn (int): sequence number
        toad (int): int or str hex of witness threshold
        baks (list): prior backers prefixes qb64
        cuts (list): witness prefixes to cut qb64
        adds (list): witness prefixes to add qb64
        version (Versionage): the API version
        kind (str): the event type

    Returns:
        Serder: event message Serder

    """

    if sn < 1:
        raise ValueError("Invalid sn = {} for vrt.".format(sn))

    vs = Versify(version=version, kind=kind, size=0)
    ilk = Ilks.vrt

    baks = baks if baks is not None else []
    bakset = oset(baks)
    if len(bakset) != len(baks):
        raise ValueError("Invalid baks = {}, has duplicates.".format(baks))

    cuts = cuts if cuts is not None else []
    cutset = oset(cuts)
    if len(cutset) != len(cuts):
        raise ValueError("Invalid cuts = {}, has duplicates.".format(cuts))

    if (bakset & cutset) != cutset:  # some cuts not in wits
        raise ValueError("Invalid cuts = {}, not all members in baks.".format(cuts))

    adds = adds if adds is not None else []
    addset = oset(adds)
    if len(addset) != len(adds):
        raise ValueError("Invalid adds = {}, has duplicates.".format(adds))

    if cutset & addset:  # non empty intersection
        raise ValueError("Intersecting cuts = {} and  adds = {}.".format(cuts, adds))

    if bakset & addset:  # non empty intersection
        raise ValueError("Intersecting baks = {} and  adds = {}.".format(baks, adds))

    newbakset = (bakset - cutset) | addset

    if len(newbakset) != (len(baks) - len(cuts) + len(adds)):  # redundant?
        raise ValueError("Invalid member combination among baks = {}, cuts ={}, "
                         "and adds = {}.".format(baks, cuts, adds))

    if isinstance(toad, str):
        toad = "{:x}".format(toad)
    elif toad is None:
        if not newbakset:
            toad = 0
        else:  # compute default f and m for len(newbakset)
            toad = ample(len(newbakset))

    if newbakset:
        if toad < 1 or toad > len(newbakset):  # out of bounds toad
            raise ValueError("Invalid toad = {} for resultant wits = {}"
                             "".format(toad, list(newbakset)))
    else:
        if toad != 0:  # invalid toad
            raise ValueError("Invalid toad = {} for resultant wits = {}"
                             "".format(toad, list(newbakset)))

    ked = dict(v=vs,  # version string
               i=regk,  # qb64 prefix
               p=dig,
               s="{:x}".format(sn),  # hex string no leading zeros lowercase
               t=ilk,
               bt="{:x}".format(toad),  # hex string no leading zeros lowercase
               br=cuts,  # list of qb64 may be empty
               ba=adds,  # list of qb64 may be empty
               )

    return Serder(ked=ked)  # return serialized ked


def issue(
        vcdig,
        regk,
        version=Version,
        kind=Serials.json,
        dt=None
):
    """ Returns serder of issuance (iss) message event

    Returns serder of iss message event
    Utility function to create a VC issuance event

    Parameters:
        vcdig (str): qb64 SAID of credential
        regk (str): qb64 AID of credential registry
        version (Versionage): the API version
        kind (str): the event type
        dt (str): ISO 8601 formatted date string of issuance date

    Returns:
        Serder: event message Serder

    """

    vs = Versify(version=version, kind=kind, size=0)
    ked = dict(v=vs,  # version string
               i=vcdig,  # qb64 prefix
               s="{:x}".format(0),  # hex string no leading zeros lowercase
               t=Ilks.iss,
               ri=regk,
               dt=helping.nowIso8601()
               )

    if dt is not None:
        ked["dt"] = dt

    return Serder(ked=ked)  # return serialized ked


def revoke(
        vcdig,
        regk,
        dig,
        version=Version,
        kind=Serials.json,
        dt=None
):
    """ Returns serder of backerless credential revocation (rev) message event

    Returns serder of rev message event
    Utility function to create a VC revocation vent

    Parameters:
        vcdig (str): qb64 SAID of credential
        regk (str): qb64 AID of credential registry
        dig (str): digest of previous event qb64
        version (Versionage): the API version
        kind (str): the event type
        dt (str): ISO 8601 formatted date string of revocation date

    Returns:
        Serder: event message Serder

    """

    vs = Versify(version=version, kind=kind, size=0)
    isn = 1
    ilk = Ilks.rev

    ked = dict(v=vs,
               i=vcdig,
               s="{:x}".format(isn),  # hex string no leading zeros lowercase
               t=ilk,
               ri=regk,
               p=dig,
               dt=helping.nowIso8601()
               )

    if dt is not None:
        ked["dt"] = dt

    return Serder(ked=ked)  # return serialized ked


def backerIssue(
        vcdig,
        regk,
        regsn,
        regd,
        version=Version,
        kind=Serials.json,
        dt=None,
):
    """ Returns serder of backer issuance (bis) message event

    Returns serder of bis message event
    Utility function to create a VC issuance event

    Parameters:
        vcdig (str): qb64 SAID of credential
        regk (str): qb64 AID of credential registry
        regsn (int): sequence number of anchoring registry TEL event
        regd (str): digest qb64 of anchoring registry TEL event
        version (Versionage): the API version
        kind (str): the event type
        dt (str): ISO 8601 formatted date string of issuance date

    Returns:
        Serder: event message Serder

    """

    vs = Versify(version=version, kind=kind, size=0)
    isn = 0
    ilk = Ilks.bis

    seal = SealEvent(regk, regsn, regd)

    ked = dict(v=vs,  # version string
               i=vcdig,  # qb64 prefix
               ii=regk,
               s="{:x}".format(isn),  # hex string no leading zeros lowercase
               t=ilk,
               ra=seal._asdict(),
               dt=helping.nowIso8601(),
               )

    if dt is not None:
        ked["dt"] = dt

    return Serder(ked=ked)  # return serialized ked


def backerRevoke(
        vcdig,
        regk,
        regsn,
        regd,
        dig,
        version=Version,
        kind=Serials.json,
        dt=None
):
    """ Returns serder of backer credential revocation (brv) message event

    Returns serder of brv message event
    Utility function to create a VC revocation event

    Parameters:
        vcdig (str): qb64 SAID of credential
        regk (str): qb64 AID of credential registry
        regsn (int): sequence number of anchoring registry TEL event
        regd (str): digest qb64 of anchoring registry TEL event
        dig (str) digest of previous event qb64
        version (Versionage): the API version
        kind (str): the event type
        dt (str): ISO 8601 formatted date string of issuance date

    Returns:
        Serder: event message Serder

    """

    vs = Versify(version=version, kind=kind, size=0)
    isn = 1
    ilk = Ilks.brv

    seal = SealEvent(regk, regsn, regd)

    ked = dict(v=vs,
               i=vcdig,
               s="{:x}".format(isn),  # hex string no leading zeros lowercase
               t=ilk,
               p=dig,
               ra=seal._asdict(),
               dt=helping.nowIso8601(),
               )

    if dt is not None:
        ked["dt"] = dt

    return Serder(ked=ked)  # return serialized ked


def state(pre,
          dig,
          sn,
          ri,
          eilk,
          br,
          ba,
          a,
          dts=None,  # default current datetime
          toad=None,  # default based on wits
          wits=None,  # default to []
          cnfg=None,  # default to []
          version=Version,
          kind=Serials.json,
          ):
    """
    Returns serder of key state notification message.
    Utility function to automate creation of rotation events.

    Parameters:
        pre (str): identifier prefix qb64
        sn (int): int sequence number of latest event
        dig (str): digest of latest event
        ri (str): qb64 AID of credential registry
        eilk (str): message type (ilk) oflatest event
        br (list): witness remove list (cuts)
        ba (list): witness add list (adds)
        dts (str) ISO 8601 formated current datetime
        toad (int): int of witness threshold
        wits (str): list of witness prefixes qb64
        cnfg (list): list of strings TraitDex of configuration traits
        version (str): Version instance
        kind (str): serialization kind

    Returns:
        Serder: Event message Serder

    Key State Dict
    {
        "v": "KERI10JSON00011c_",
        "i": "EaU6JR2nmwyZ-i0d8JZAoTNZH3ULvYAfSVPzhzS6b5CM",
        "s": "2":,
        "p": "EYAfSVPzhzZ-i0d8JZS6b5CMAoTNZH3ULvaU6JR2nmwy",
        "d": "EAoTNZH3ULvaU6JR2nmwyYAfSVPzhzZ-i0d8JZS6b5CM",
        "ri": "EYAfSVPzhzZ-i0d8JZS6b5CMAoTNZH3ULvaU6JR2nmwy",
        "dt": "2020-08-22T20:35:06.687702+00:00",
        "et": "vrt",
        "a": {i=12, d="EYAfSVPzhzS6b5CMaU6JR2nmwyZ-i0d8JZAoTNZH3ULv"},
        "k": ["DaU6JR2nmwyZ-i0d8JZAoTNZH3ULvYAfSVPzhzS6b5CM"],
        "n": "EZ-i0d8JZAoTNZH3ULvaU6JR2nmwyYAfSVPzhzS6b5CM",
        "bt": "1",
        "b": ["DnmwyYAfSVPzhzS6b5CMZ-i0d8JZAoTNZH3ULvaU6JR2"],
        "br": ["Dd8JZAoTNZH3ULvaU6JR2nmwyYAfSVPzhzS6b5CMZ-i0"],
        "ba": ["DnmwyYAfSVPzhzS6b5CMZ-i0d8JZAoTNZH3ULvaU6JR2"]
        "di": "EYAfSVPzhzS6b5CMaU6JR2nmwyZ-i0d8JZAoTNZH3ULv",
        "c": ["eo"],
    }

    """
    vs = Versify(version=version, kind=kind, size=0)

    if sn < 0:
        raise ValueError("Negative sn = {} in key state.".format(sn))

    if eilk not in (Ilks.vcp, Ilks.vrt):
        raise ValueError("Invalid evernt type et=  in key state.".format(eilk))

    if dts is None:
        dts = helping.nowIso8601()

    wits = wits if wits is not None else []
    witset = oset(wits)
    if len(witset) != len(wits):
        raise ValueError("Invalid wits = {}, has duplicates.".format(wits))

    if toad is None:
        if not witset:
            toad = 0
        else:
            toad = max(1, ceil(len(witset) / 2))

    if witset:
        if toad < 1 or toad > len(witset):  # out of bounds toad
            raise ValueError("Invalid toad = {} for resultant wits = {}"
                             "".format(toad, list(witset)))
    else:
        if toad != 0:  # invalid toad
            raise ValueError("Invalid toad = {} for resultant wits = {}"
                             "".format(toad, list(witset)))

    cnfg = cnfg if cnfg is not None else []

    if len(oset(br)) != len(br):  # duplicates in cuts
        raise ValueError("Invalid cuts = {} in latest est event, has duplicates"
                         ".".format(br))

    if len(oset(ba)) != len(ba):  # duplicates in adds
        raise ValueError("Invalid adds = {} in latest est event, has duplicates"
                         ".".format(ba))

    ksd = dict(v=vs,  # version string
               i=ri,  # qb64 SAID of the registry
               s="{:x}".format(sn),  # lowercase hex string no leading zeros
               d=dig,
               ii=pre,
               dt=dts,
               et=eilk,
               a=a,
               bt="{:x}".format(toad),  # hex string no leading zeros lowercase
               br=br,
               ba=ba,
               b=wits,  # list of qb64 may be empty
               c=cnfg,  # list of config ordered mappings may be empty
               )

    return Serder(ked=ksd)  # return serialized ksd


def vcstate(vcpre,
            dig,
            sn,
            ri,
            eilk,
            a,
            dts=None,  # default current datetime
            version=Version,
            kind=Serials.json,
            ):
    """
    Returns serder of credential transaction state notification message.
    Utility function to automate creation of tsn events.

    Parameters:
        pre is identifier prefix qb64 of the issuer of the credential
        sn is int sequence number of latest event
        dig is digest of latest event
        eilk is message type (ilk) oflatest event
        version is Version instance
        kind is serialization kind

    Credential Transaction State Dict
    {
        "v": "KERI10JSON00011c_",
        "i": "EaU6JR2nmwyZ-i0d8JZAoTNZH3ULvYAfSVPzhzS6b5CM",
        "s": "2":,
        "t": "ksn",
        "d": "EAoTNZH3ULvaU6JR2nmwyYAfSVPzhzZ-i0d8JZS6b5CM",
        "ri": "EYAfSVPzhzZ-i0d8JZS6b5CMAoTNZH3ULvaU6JR2nmwy",
        "dt": "2020-08-22T20:35:06.687702+00:00",
        "et": "rev",
    }

    """

    vs = Versify(version=version, kind=kind, size=0)

    if sn < 0:
        raise ValueError("Negative sn = {} in key state.".format(sn))

    if eilk not in (Ilks.iss, Ilks.bis, Ilks.rev, Ilks.brv):
        raise ValueError("Invalid evernt type et=  in key state.".format(eilk))

    if dts is None:
        dts = helping.nowIso8601()

    ksd = dict(v=vs,  # version string
               i=vcpre,  # qb64 prefix
               s="{:x}".format(sn),  # lowercase hex string no leading zeros
               d=dig,
               ri=ri,
               a=a,
               dt=dts,
               et=eilk,
               )

    return Serder(ked=ksd)  # return serialized ksd


def query(regk,
          vcid,
          route="",
          replyRoute="",
          dt=None,
          dta=None,
          dtb=None,
          stamp=None,
          version=Version,
          kind=Serials.json
          ):
    """ Returns serder of credentialquery (qry) event message.

    Returns serder of query event message.
    Utility function to automate creation of interaction events.

     Parameters:
         regk (str): qb64 AID of credential registry
         vcid (str): qb64 SAID of credential
         route (str): namesapaced path, '/' delimited, that indicates data flow
                      handler (behavior) to processs the query
         replyRoute (str): namesapaced path, '/' delimited, that indicates data flow
                      handler (behavior) to processs reply message to query if any.
         dt (str): ISO 8601 formatted datetime query
         dta (str): ISO 8601 formatted datetime after query
         dtb (str): ISO 8601 formatted datetime before query
         stamp (str): ISO 8601 formatted current datetime of query message
         version (Versionage): the API version
         kind (str): the event type

     Returns:
         Serder: query event message Serder

    """
    qry = dict(i=vcid, ri=regk)

    if dt is not None:
        qry["dt"] = dt

    if dta is not None:
        qry["dta"] = dt

    if dtb is not None:
        qry["dtb"] = dt

    return core.eventing.query(route=route,
                               replyRoute=replyRoute,
                               query=qry,
                               stamp=stamp,
                               version=version,
                               kind=kind)


class Tever:
    """
    Tever is KERI transaction event verifier class
    Only supports current version VERSION

    Has the following public attributes and properties:

    Class Attributes:
        .NoBackers is Boolean
                True means do not allow backers (default to witnesses of controlling KEL)
                False means allow backers (ignore witnesses of controlling KEL)

    Attributes:
        .db is reference to Baser instance that managers the LMDB database
        .reg is regerence to Registry instance that manages VC LMDB database
        .regk is fully qualified base64 identifier prefix of own Registry if any
        .local is Boolean
            True means only process msgs for own events if .regk
            False means only process msgs for not own events if .regk
        .version is version of current event state
        .prefixer is prefixer instance fParemtersor current event state
        .sn is sequence number int
        .serder is Serder instance of current event with .serder.diger for digest
        .toad is int threshold of accountable duplicity
        .baks is list of qualified qb64 aids for backers
        .cuts is list of qualified qb64 aids for backers cut from prev wits list
        .adds is list of qualified qb64 aids for backers added to prev wits list
        .noBackers is boolean trait True means do not allow backers

    """
    NoBackers = False

    def __init__(self, cues=None, state=None, serder=None, seqner=None, diger=None, bigers=None, db=None,
                 reger=None, noBackers=None, regk=None, local=False):
        """ Create incepting tever and state from registry inception serder

        Create incepting tever and state from registry inception serder

        Parameters:
            serder (Serder): instance of registry inception event
            state (Serder): transaction state notice state message Serder
            seqner (Seqner): issuing event sequence number from controlling KEL.
            diger (Diger): issuing event digest from controlling KEL.
            bigers (list): list of Siger instances of indexed backer signatures of
                event. Index is offset into baks list of latest est event
            db (Baser): instance of baser lmdb database
            reger (Registry): instance of VC lmdb database
            noBackers (bool): True means do not allow backer configuration
            regk (str): identifier prefix of own or local registry. May not be the
                prefix of this Tever's event. Some restrictions if present
            local (bool): True means only process msgs for own controller's
                events if .regk. False means only process msgs for not own events
                if .regk

        Returns:
            Tever:  instance representing credential Registry

        """

        if not (state or serder):
            raise ValueError("Missing required arguments. Need state or serder")

        self.reger = reger if reger is not None else Registry()
        self.cues = cues if cues is not None else decking.Deck()

        self.db = db if db is not None else basing.Baser(reopen=True)
        self.local = True if local else False

        if state:  # preload from state
            self.reload(state)
            return

        self.version = serder.version
        self.regk = regk

        ilk = serder.ked["t"]
        if ilk not in [Ilks.vcp]:
            raise ValidationError("Expected ilk {} got {} for evt: {}".format(Ilks.vcp, ilk, serder))

        self.ilk = ilk
        labels = VCP_LABELS
        for k in labels:
            if k not in serder.ked:
                raise ValidationError("Missing element = {} from {} event for "
                                      "evt = {}.".format(k, ilk, serder.ked))

        self.incept(serder=serder)

        self.config(serder=serder, noBackers=noBackers)

        bigers = self.valAnchorBigs(serder=serder,
                                    seqner=seqner,
                                    diger=diger,
                                    bigers=bigers,
                                    toad=self.toad,
                                    baks=self.baks)

        self.logEvent(pre=self.prefixer.qb64b,
                      sn=0,
                      serder=serder,
                      seqner=seqner,
                      diger=diger,
                      bigers=bigers,
                      baks=self.baks)

        self.regk = self.prefixer.qb64
        self.reger.states.pin(keys=self.regk, val=self.state())


    def reload(self, ksn):
        """ Reload Tever attributes (aka its state) from state serder

        Reload Tever attributes (aka its state) from state serder

        Parameters:
            ksn (Serder): instance of key stat notice 'ksn' message body

        """

        for k in TSN_LABELS:
            if k not in ksn.ked:
                raise ValidationError("Missing element = {} from {} event."
                                      " evt = {}.".format(k, Ilks.ksn,
                                                          ksn.pretty()))

        self.version = ksn.version
        self.pre = ksn.pre
        self.regk = ksn.ked["ri"]
        self.prefixer = Prefixer(qb64=self.regk)
        self.sn = ksn.sn
        self.ilk = ksn.ked["et"]
        self.toad = int(ksn.ked["bt"], 16)
        self.baks = ksn.ked["b"]
        self.cuts = ksn.ked["br"]
        self.adds = ksn.ked["ba"]

        self.noBackers = True if TraitDex.NoBackers in ksn.ked["c"] else False

        if (raw := self.reger.getTvt(key=dgKey(pre=self.prefixer.qb64,
                                               dig=ksn.ked['d']))) is None:
            raise kering.MissingEntryError("Corresponding event for state={} not found."
                                           "".format(ksn.pretty()))
        self.serder = Serder(raw=bytes(raw))


    def state(self, kind=Serials.json):
        """ Returns Serder instance of current transaction state notification message

        Returns Serder instance of current transaction state notification message of this
        credential registry.

        Parameters:
            kind (str): serialization kind for message json, cbor, mgpk

        Returns:
            Serder:  event message Serder instance

        """
        br = self.cuts
        ba = self.adds

        cnfg = []
        if self.noBackers:
            cnfg.append(TraitDex.NoBackers)

        dgkey = dbing.dgKey(self.regk, self.serder.dig)
        couple = self.reger.getAnc(dgkey)
        ancb = bytearray(couple)
        seqner = coring.Seqner(qb64b=ancb, strip=True)
        diger = coring.Diger(qb64b=ancb, strip=True)

        return (state(pre=self.pre,
                      dig=self.serder.dig,
                      sn=self.sn,
                      ri=self.regk,
                      dts=None,
                      eilk=self.ilk,
                      a=dict(s=seqner.sn, d=diger.qb64),
                      br=br,
                      ba=ba,
                      toad=self.toad,
                      wits=self.baks,
                      cnfg=cnfg,
                      kind=kind
                      )
                )

    def incept(self, serder):
        """  Validate registry inception event and initialize local attributes

        Parse and validate registry inception event for this Tever.  Update all
        local attributes with initial values.

        Parameters:
            serder (Serder): registry inception event (vcp)

        """

        ked = serder.ked
        self.pre = ked["ii"]
        self.prefixer = Prefixer(qb64=serder.pre)
        if not self.prefixer.verify(ked=ked, prefixed=True):  # invalid prefix
            raise ValidationError("Invalid prefix = {} for registry inception evt = {}."
                                  .format(self.prefixer.qb64, ked))

        sn = ked["s"]
        self.sn = validateSN(sn, inceptive=True)

        self.cuts = []  # always empty at inception since no prev event
        self.adds = []  # always empty at inception since no prev event
        baks = ked["b"]
        if len(oset(baks)) != len(baks):
            raise ValidationError("Invalid baks = {}, has duplicates for evt = {}."
                                  "".format(baks, ked))
        self.baks = baks

        toad = int(ked["bt"], 16)
        if baks:
            if toad < 1 or toad > len(baks):  # out of bounds toad
                raise ValidationError("Invalid toad = {} for baks = {} for evt = {}."
                                      "".format(toad, baks, ked))
        else:
            if toad != 0:  # invalid toad
                raise ValidationError("Invalid toad = {} for baks = {} for evt = {}."
                                      "".format(toad, baks, ked))
        self.toad = toad
        self.serder = serder

    def config(self, serder, noBackers=None):
        """ Process cnfg field for configuration traits

        Parse and validate the configuration options for registry inception from
        the `c` field of the provided inception event.

        Parameters:
            serder (Serder): credential registry inception event `vcp`
            noBackers (bool): override flag for specifying a registry with no additional backers
                              beyond the controlling KEL's witnesses


        """
        # assign traits
        self.noBackers = (True if (noBackers if noBackers is not None
                                   else self.NoBackers)
                          else False)  # ensure default noBackers is boolean

        cnfg = serder.ked["c"]  # process cnfg for traits
        if TraitDex.NoBackers in cnfg:
            self.noBackers = True

    def update(self, serder, seqner=None, diger=None, bigers=None):
        """ Process registry non-inception events.

        Process non-inception registry and credential events and update local
        Tever state for registry or credential

        Parameters:
            serder (Serder): instance of issuance or backer issuance event
            seqner (Seqner): issuing event sequence number from controlling KEL.
            diger (Diger): issuing event digest from controlling KEL.
            bigers (list): of Siger instances of indexed witness signatures.
                Index is offset into wits list of associated witness nontrans pre
                from which public key may be derived.

        """

        ked = serder.ked
        ilk = ked["t"]
        sn = ked["s"]

        icp = ilk in (Ilks.iss, Ilks.bis)

        # validate SN for
        sn = validateSN(sn, inceptive=icp)

        if ilk in (Ilks.vrt,):
            if self.noBackers is True:
                raise ValidationError("invalid rotation evt {} against backerless registry {}".
                                      format(ked, self.regk))
            toad, baks, cuts, adds = self.rotate(serder, sn=sn)

            bigers = self.valAnchorBigs(serder=serder,
                                        seqner=seqner,
                                        diger=diger,
                                        bigers=bigers,
                                        toad=toad,
                                        baks=baks)

            self.sn = sn
            self.serder = serder
            self.ilk = ilk
            self.toad = toad
            self.baks = baks
            self.cuts = cuts
            self.adds = adds

            self.logEvent(pre=self.prefixer.qb64b,
                          sn=sn,
                          serder=serder,
                          seqner=seqner,
                          diger=diger,
                          bigers=bigers,
                          baks=self.baks)
            self.reger.states.pin(keys=self.regk, val=self.state())

            return

        elif ilk in (Ilks.iss, Ilks.bis):
            self.issue(serder, seqner=seqner, diger=diger, sn=sn, bigers=bigers)
        elif ilk in (Ilks.rev, Ilks.brv):
            self.revoke(serder, seqner=seqner, diger=diger, sn=sn, bigers=bigers)
        else:  # unsupported event ilk so discard
            raise ValidationError("Unsupported ilk = {} for evt = {}.".format(ilk, ked))


    def rotate(self, serder, sn):
        """ Process registry management TEL, non-inception events (vrt)

        Parameters:
            serder (Serder): registry rotation event
            sn (int): sequence number of event

        Returns:
            int: calculated backer threshold
            list: new list of backers after applying cuts and adds to previous list
            list: list of backer adds processed from event
            list: list of backer cuts processed from event

        """

        ked = serder.ked
        dig = ked["p"]

        if serder.pre != self.prefixer.qb64:
            raise ValidationError("Mismatch event aid prefix = {} expecting"
                                  " = {} for evt = {}.".format(ked["i"],
                                                               self.prefixer.qb64,
                                                               ked))
        if not sn == (self.sn + 1):  # sn not in order
            raise ValidationError("Invalid sn = {} expecting = {} for evt "
                                  "= {}.".format(sn, self.sn + 1, ked))

        if not self.serder.compare(dig=dig):  # prior event dig not match
            raise ValidationError("Mismatch event dig = {} with state dig"
                                  " = {} for evt = {}.".format(ked["p"],
                                                               self.serder.diger.qb64,
                                                               ked))

        witset = oset(self.baks)
        cuts = ked["br"]
        cutset = oset(cuts)
        if len(cutset) != len(cuts):
            raise ValidationError("Invalid cuts = {}, has duplicates for evt = "
                                  "{}.".format(cuts, ked))

        if (witset & cutset) != cutset:  # some cuts not in baks
            raise ValidationError("Invalid cuts = {}, not all members in baks"
                                  " for evt = {}.".format(cuts, ked))

        adds = ked["ba"]
        addset = oset(adds)
        if len(addset) != len(adds):
            raise ValidationError("Invalid adds = {}, has duplicates for evt = "
                                  "{}.".format(adds, ked))

        if cutset & addset:  # non empty intersection
            raise ValidationError("Intersecting cuts = {} and  adds = {} for "
                                  "evt = {}.".format(cuts, adds, ked))

        if witset & addset:  # non empty intersection
            raise ValidationError("Intersecting baks = {} and  adds = {} for "
                                  "evt = {}.".format(self.baks, adds, ked))

        baks = list((witset - cutset) | addset)

        if len(baks) != (len(self.baks) - len(cuts) + len(adds)):  # redundant?
            raise ValidationError("Invalid member combination among baks = {}, cuts ={}, "
                                  "and adds = {} for evt = {}.".format(self.baks,
                                                                       cuts,
                                                                       adds,
                                                                       ked))

        toad = int(ked["bt"], 16)
        if baks:
            if toad < 1 or toad > len(baks):  # out of bounds toad
                raise ValidationError("Invalid toad = {} for baks = {} for evt "
                                      "= {}.".format(toad, baks, ked))
        else:
            if toad != 0:  # invalid toad
                raise ValidationError("Invalid toad = {} for baks = {} for evt "
                                      "= {}.".format(toad, baks, ked))

        return toad, baks, cuts, adds

    def issue(self, serder, seqner, diger, sn, bigers=None):
        """ Process VC TEL issuance events (iss, bis)

        Validate and process credential issuance events.  If valid, event is persisted
        in local datastore for TEL.  Will escrow event if missing anchor or backer signatures

        Parameters
            serder (Serder): instance of issuance or backer issuance event
            seqner (Seqner): issuing event sequence number from controlling KEL.
            diger (Diger): issuing event digest from controlling KEL.
            sn (int): event sequence event
            bigers (list): of Siger instances of indexed witness signatures.
                Index is offset into wits list of associated witness nontrans pre
                from which public key may be derived.

        """

        ked = serder.ked
        vcpre = ked["i"]
        ilk = ked["t"]
        vci = nsKey([self.prefixer.qb64, vcpre])

        labels = ISS_LABELS if ilk == Ilks.iss else BIS_LABELS

        for k in labels:
            if k not in ked:
                raise ValidationError("Missing element = {} from {} event for "
                                      "evt = {}.".format(k, ilk, ked))

        if ilk == Ilks.iss:  # simple issue
            if self.noBackers is False:
                raise ValidationError("invalid simple issue evt {} against backer based registry {}".
                                      format(ked, self.regk))

            regi = ked["ri"]
            if regi != self.prefixer.qb64:
                raise ValidationError("Mismatch event regi prefix = {} expecting"
                                      " = {} for evt = {}.".format(regi,
                                                                   self.prefixer.qb64,
                                                                   ked))

            # check if fully anchored
            if not self.verifyAnchor(serder=serder, seqner=seqner, diger=diger):
                if self.escrowALEvent(serder=serder, seqner=seqner, diger=diger):
                    self.cues.append(dict(kin="query", q=dict(pre=self.pre, sn=seqner.sn)))
                raise MissingAnchorError("Failure verify event = {} "
                                         "".format(serder.ked,
                                                   ))

            self.logEvent(pre=vci, sn=sn, serder=serder, seqner=seqner, diger=diger)

        elif ilk == Ilks.bis:  # backer issue
            if self.noBackers is True:
                raise ValidationError("invalid backer issue evt {} against backerless registry {}".
                                      format(ked, self.regk))

            rtoad, baks = self.getBackerState(ked)
            bigers = self.valAnchorBigs(serder=serder,
                                        seqner=seqner,
                                        diger=diger,
                                        bigers=bigers,
                                        toad=rtoad,
                                        baks=baks)

            self.logEvent(pre=vci, sn=sn, serder=serder, seqner=seqner, diger=diger, bigers=bigers)

        else:
            raise ValidationError("Unsupported ilk = {} for evt = {}.".format(ilk, ked))

    def revoke(self, serder, seqner, diger, sn, bigers=None):
        """ Process VC TEL revocation events (rev, brv)

        Validate and process credential revocation events.  If valid, event is persisted
        in local datastore for TEL.  Will escrow event if missing anchor or backer signatures

        Parameters
            serder (Serder): instance of issuance or backer issuance event
            seqner (Seqner): issuing event sequence number from controlling KEL.
            diger (Diger): issuing event digest from controlling KEL.
            sn (int): event sequence event
            bigers (list): of Siger instances of indexed witness signatures.
                Index is offset into wits list of associated witness nontrans pre
                from which public key may be derived.

        """

        ked = serder.ked
        vcpre = ked["i"]
        ilk = ked["t"]

        labels = REV_LABELS if ilk == Ilks.rev else BRV_LABELS

        for k in labels:
            if k not in ked:
                raise ValidationError("Missing element = {} from {} event for "
                                      "evt = {}.".format(k, ilk, ked))

        # have to compare with VC issuance serder
        vci = nsKey([self.prefixer.qb64, vcpre])

        dig = self.reger.getTel(snKey(pre=vci, sn=sn - 1))
        ievt = self.reger.getTvt(dgKey(pre=vci, dig=dig))
        if ievt is None:
            raise ValidationError("revoke without issue... probably have to escrow")

        ievt = bytes(ievt)
        iserder = Serder(raw=ievt)
        if not iserder.compare(dig=ked["p"]):  # prior event dig not match
            raise ValidationError("Mismatch event dig = {} with state dig"
                                  " = {} for evt = {}.".format(ked["p"],
                                                               self.serder.diger.qb64,
                                                               ked))

        if ilk in (Ilks.rev,):  # simple revoke
            if self.noBackers is False:
                raise ValidationError("invalid simple issue evt {} against backer based registry {}".
                                      format(ked, self.regk))

            # check if fully anchored
            if not self.verifyAnchor(serder=serder, seqner=seqner, diger=diger):
                if self.escrowALEvent(serder=serder, seqner=seqner, diger=diger):
                    self.cues.append(dict(kin="query", q=dict(pre=self.pre, sn=seqner.sn)))
                raise MissingAnchorError("Failure verify event = {} "
                                         "".format(serder.ked))

            self.logEvent(pre=vci, sn=sn, serder=serder, seqner=seqner, diger=diger)

        elif ilk in (Ilks.brv,):  # backer revoke
            if self.noBackers is True:
                raise ValidationError("invalid backer issue evt {} against backerless registry {}".
                                      format(ked, self.regk))

            rtoad, baks = self.getBackerState(ked)
            bigers = self.valAnchorBigs(serder=serder,
                                        seqner=seqner,
                                        diger=diger,
                                        bigers=bigers,
                                        toad=rtoad,
                                        baks=baks)

            self.logEvent(pre=vci, sn=sn, serder=serder, seqner=seqner, diger=diger, bigers=bigers)

        else:
            raise ValidationError("Unsupported ilk = {} for evt = {}.".format(ilk, ked))

    def vcState(self, vcpre):
        """ Calculate state (issued/revoked) of VC from db.

        Returns None if never issued from this Registry

        Parameters:
          vcpre (str):  qb64 VC identifier

        Returns:
            status (str): `issued` or `revoked` or None if credential identifier is not found
        """
        vci = nsKey([self.prefixer.qb64, vcpre])
        digs = []
        for _, dig in self.reger.getTelItemPreIter(pre=vci):
            digs.append(dig)

        if len(digs) == 0:
            return None

        vcsn = len(digs) - 1
        vcdig = bytes(digs[-1])
        if self.noBackers:
            vcilk = Ilks.iss if len(digs) == 1 else Ilks.rev
        else:
            vcilk = Ilks.bis if len(digs) == 1 else Ilks.brv

        dgkey = dbing.dgKey(vci, vcdig)
        couple = self.reger.getAnc(dgkey)
        ancb = bytearray(couple)
        seqner = coring.Seqner(qb64b=ancb, strip=True)
        diger = coring.Diger(qb64b=ancb, strip=True)

        return vcstate(vcpre=vcpre,
                       dig=vcdig.decode("utf-8"),
                       sn=vcsn,
                       ri=self.prefixer.qb64,
                       eilk=vcilk,
                       a=dict(s=seqner.sn, d=diger.qb64),
                       )

    def vcSn(self, vcpre):
        """ Calculates the current seq no of VC from db.

        Returns None if never issued from this Registry

        Parameters:
          vcpre (str):  qb64 VC identifier

        Returns:
            int: current TEL sequence number of credential or None if not found

        """
        vci = nsKey([self.prefixer.qb64, vcpre])
        cnt = self.reger.cntTels(vci)

        return None if cnt == 0 else cnt - 1

    def logEvent(self, pre, sn, serder, seqner, diger, bigers=None, baks=None):
        """ Update associated logs for verified event.

        Update is idempotent. Logs will not write dup at key if already exists.

        Parameters:
            pre (qb64): is event prefix
            sn (int): is event sequence number
            serder (Serder): is Serder instance of current event
            seqner (Seqner): issuing event sequence number from controlling KEL.
            seqner (Seqner): is optional Seqner instance of cloned first seen ordinal
                If cloned mode then seqner maybe provided (not None)
                When seqner provided then compare fn of dater and database and
                first seen if not match then log and add cue notify problem
            diger (Diger): issuing event digest from controlling KEL.
            bigers (list): is optional list of Siger instance of indexed backer sigs
            baks (list): is optional list of qb64 non-trans identifiers of backers
        """

        dig = serder.diger.qb64b
        key = dgKey(pre, dig)
        sealet = seqner.qb64b + diger.qb64b
        self.reger.putAnc(key, sealet)
        if bigers:
            self.reger.putTibs(key, [biger.qb64b for biger in bigers])
        if baks:
            self.reger.delBaks(key)
            self.reger.putBaks(key, [bak.encode("utf-8") for bak in baks])
        self.reger.tets.pin(keys=(pre.decode("utf-8"), dig.decode("utf-8")), val=coring.Dater())
        self.reger.putTvt(key, serder.raw)
        self.reger.putTel(snKey(pre, sn), dig)
        logger.info("Tever state: %s Added to TEL valid event=\n%s\n",
                    pre, json.dumps(serder.ked, indent=1))

    def valAnchorBigs(self, serder, seqner, diger, bigers, toad, baks):
        """ Validate anchor and backer signatures (bigers) when provided.

        Validates sigers signatures by validating indexes, verifying signatures, and
            validating threshold sith.
        Validate backer receipts by validating indexes, verifying
            backer signatures and validating toad.
        Backer validation is a function of .regk and .local

        Parameters:
            serder (Serder): instance of event
            seqner (Seqner): issuing event sequence number from controlling KEL.
            diger (Diger): issuing event digest from controlling KEL.
            bigers (list)  Siger instances of indexed witness signatures.
                Index is offset into wits list of associated witness nontrans pre
                from which public key may be derived.
            toad (int):  str hex of witness threshold
            baks (list): qb64 non-transferable prefixes of backers used to
                derive werfers for bigers

        Returns:
            list: unique validated signature verified members of inputed bigers

        """

        berfers = [Verfer(qb64=bak) for bak in baks]

        # get unique verified bigers and bindices lists from bigers list
        bigers, bindices = verifySigs(serder=serder, sigers=bigers, verfers=berfers)
        # each biger now has werfer of corresponding wit

        # check if fully anchored
        if not self.verifyAnchor(serder=serder, seqner=seqner, diger=diger):
            if self.escrowALEvent(serder=serder, seqner=seqner, diger=diger, bigers=bigers, baks=baks):
                self.cues.append(dict(kin="query", q=dict(pre=self.pre, sn=seqner.sn)))
            raise MissingAnchorError("Failure verify event = {} "
                                     "".format(serder.ked))

        # Kevery .process event logic prevents this from seeing event when
        # not local and event pre is own pre
        if ((baks and not self.regk) or  # in promiscuous mode so assume must verify toad
                (baks and not self.local and self.regk and self.regk not in baks)):
            # validate that event is fully witnessed
            if isinstance(toad, str):
                toad = int(toad, 16)
            if toad < 0 or len(baks) < toad:
                raise ValidationError("Invalid toad = {} for wits = {} for evt"
                                      " = {}.".format(toad, baks, serder.ked))

            if len(bindices) < toad:  # not fully witnessed yet
                self.escrowPWEvent(serder=serder, seqner=seqner, diger=diger, bigers=bigers)

                raise MissingWitnessSignatureError("Failure satisfying toad = {} "
                                                   "on witness sigs for {} for evt = {}.".format(toad,
                                                                                                 [siger.qb64 for siger
                                                                                                  in bigers],
                                                                                                 serder.ked))
        return bigers

    def verifyAnchor(self, serder, seqner, diger):
        """ Retrieve specified anchoring event and verify seal

        Retrieve event from db using anchor, get seal from event eserder and
        verify pre, sn and dig against serder

        Parameters:
            serder (Serder): anchored TEL event
            seqner (Seqner): sequence number of anchoring event
            diger (Diger): digest of anchoring event

        Returns:
             bool: True is anchoring event exists in database and seal is valid against
                   TEL event.

        """

        dig = self.db.getKeLast(key=snKey(pre=self.pre, sn=seqner.sn))
        if not dig:
            return False
        else:
            dig = bytes(dig)

        # retrieve event by dig
        raw = self.db.getEvt(key=dgKey(pre=self.pre, dig=dig))
        if not raw:
            return False
        else:
            raw = bytes(raw)

        eserder = Serder(raw=raw)  # deserialize event raw

        if eserder.dig != diger.qb64:
            return False

        seal = eserder.ked["a"]
        if seal is None or len(seal) != 1:
            return False

        seal = seal[0]
        spre = seal["i"]
        ssn = seal["s"]
        sdig = seal["d"]

        if spre == serder.ked["i"] and ssn == serder.ked["s"] \
                and serder.dig == sdig:
            return True

        return False

    def escrowPWEvent(self, serder, seqner, diger, bigers=None):
        """ Update associated logs for escrow of partially witnessed event

        Parameters:
            serder (Serder): instance of  event
            seqner (Seqner): sequence number for anchor seal
            diger (Diger): digest of anchor
            bigers (list): Siger instance of indexed witness sigs

        """
        dgkey = dgKey(serder.preb, serder.digb)
        sealet = seqner.qb64b + diger.qb64b
        self.reger.putAnc(dgkey, sealet)
        self.reger.putTibs(dgkey, [biger.qb64b for biger in bigers])
        self.reger.putTvt(dgkey, serder.raw)
        self.reger.putTwe(snKey(serder.preb, serder.sn), serder.digb)
        logger.info("Tever state: Escrowed partially witnessed "
                    "event = %s\n", serder.ked)


    def escrowALEvent(self, serder, seqner, diger, bigers=None, baks=None):
        """ Update associated logs for escrow of anchorless event

        Parameters:
            serder (Serder): instance of  event
            seqner (Seqner): sequence number for anchor seal
            diger (Diger): digest of anchor
            bigers (list): Siger instance of indexed witness sigs
            baks (list): qb64 of new backers

        Returns:
            bool: True if escrow is successful, False otherwith (eg. already escrowed)

        """
        key = dgKey(serder.preb, serder.digb)
        if seqner and diger:
            sealet = seqner.qb64b + diger.qb64b
            self.reger.putAnc(key, sealet)
        if bigers:
            self.reger.putTibs(key, [biger.qb64b for biger in bigers])
        if baks:
            self.reger.delBaks(key)
            self.reger.putBaks(key, [bak.encode("utf-8") for bak in baks])
        self.reger.putTvt(key, serder.raw)
        logger.info("Tever state: Escrowed anchorless event "
                    "event = %s\n", serder.ked)
        return self.reger.putTae(snKey(serder.preb, serder.sn), serder.digb)


    def getBackerState(self, ked):
        """ Calculate and return the current list of backers for event dict

        Parameters:
            ked (dict):  event dict

        Returns:
            list:  qb64 of current list of backers for state at ked

        """
        rega = ked["ra"]
        regi = rega["i"]
        regd = rega["d"]

        if regi != self.prefixer.qb64:
            raise ValidationError("Mismatch event regk prefix = {} expecting"
                                  " = {} for evt = {}.".format(self.regk,
                                                               self.prefixer.qb64,
                                                               ked))

        # load backer list and toad (via event) for specific event in registry from seal in event
        dgkey = dgKey(regi, regd)
        revt = self.reger.getTvt(dgkey)
        if revt is None:
            raise ValidationError("have to escrow this somewhere")

        rserder = Serder(raw=bytes(revt))
        # the backer threshold at this event in mgmt TEL
        rtoad = rserder.ked["bt"]

        baks = [bytes(bak) for bak in self.reger.getBaks(dgkey)]

        return rtoad, baks


class Tevery:
    """ Tevery (Transaction Event Message Processing Facility)

    Tevery processes an incoming message stream composed of KERI key event related
    messages and attachments.  Tevery acts as a Tever (transaction event verifier)
    factory for managing transaction state of KERI credential registries and associated
    credentials.

    Attributes:
        db (Baser):  local LMDB identifier database
        reger (Registry): local LMDB credential database
        regk (str): qb64 registry AID
        local (bool): True means only process msgs for own events if .regk
                        False means only process msgs for not own events if .regk
        cues (Deck): notices generated from processing events


    """

    def __init__(self, reger=None, db=None, regk=None, local=False, cues=None):
        """ Initialize instance:

        Parameters:
            reger (Registry): local LMDB credential database
            db (Baser):  local LMDB identifier database
            regk (str): local or own identifier prefix. Some restriction if present
            local (bool): True means only process msgs for own events if .regk
                        False means only process msgs for not own events if .regk
            cues (Deck): notices generated from processing events


        """
        self.db = db if db is not None else basing.Baser(reopen=True)  # default name = "main"
        self.reger = reger if reger is not None else Registry()
        self.regk = regk  # local prefix for restrictions on local events
        self.local = True if local else False  # local vs nonlocal restrictions
        self.cues = cues if cues is not None else decking.Deck()

    @property
    def tevers(self):
        """ Returns .reger.tevers read through cache of credential registries """

        return self.reger.tevers


    def processEvent(self, serder, seqner, diger, wigers=None):
        """ Process one event serder with attached indexde signatures sigers

        Validates event against current state of registry or credential, creating registry
        on inception events and processing change in state to credential or registry for
        other events

        Parameters:
            serder (Serder): event to process
            seqner (Seqner): issuing event sequence number from controlling KEL.
            diger (Diger): issuing event digest from controlling KEL.
            wigers (list): optional list of Siger instances of attached witness indexed sigs

        """
        ked = serder.ked
        try:  # see if code of pre is supported and matches size of pre
            Prefixer(qb64b=serder.preb)
        except Exception:  # if unsupported code or bad size raises error
            raise ValidationError("Invalid pre = {} for evt = {}."
                                  "".format(serder.pre, ked))

        regk = self.registryKey(serder)
        pre = serder.pre
        ked = serder.ked
        sn = ked["s"]
        ilk = ked["t"]

        inceptive = ilk in (Ilks.vcp, Ilks.iss, Ilks.bis)

        # validate SN for
        sn = validateSN(sn, inceptive=inceptive)

        if self.regk:
            if self.local:
                if self.regk != regk:  # nonlocal event when in local mode
                    raise ValueError("Nonlocal event regk={} when local mode for regk={}."
                                     "".format(regk, self.regk))
            else:
                if self.regk == regk:  # local event when not in local mode
                    raise ValueError("Local event regk={} when nonlocal mode."
                                     "".format(regk))

        if regk not in self.tevers:  # first seen for this registry
            if ilk in [Ilks.vcp]:
                # incepting a new registry, Tever create will validate anchor, etc.
                tever = Tever(serder=serder,
                              seqner=seqner,
                              diger=diger,
                              bigers=wigers,
                              reger=self.reger,
                              db=self.db,
                              regk=self.regk,
                              local=self.local,
                              cues=self.cues)
                self.tevers[regk] = tever
                if not self.regk or self.regk != regk:
                    # witness style backers will need to send receipts so lets queue them up for now
                    # actually, lets not because the Kevery has no idea what to do with them!
                    # self.cues.append(dict(kin="receipt", serder=serder))
                    pass
            else:
                # out of order, need to escrow
                self.escrowOOEvent(serder=serder, seqner=seqner, diger=diger)
                raise OutOfOrderError("escrowed out of order event {}".format(ked))

        else:
            if ilk in (Ilks.vcp,):
                # we don't have multiple signatures to verify so this
                # is already first seen and then lifely duplicitious
                raise LikelyDuplicitousError("Likely Duplicitous event={}.".format(ked))

            tever = self.tevers[regk]
            tever.cues = self.cues
            if ilk in [Ilks.vrt]:
                sno = tever.sn + 1  # proper sn of new inorder event
            else:
                esn = tever.vcSn(pre)
                sno = 0 if esn is None else esn + 1

            if sn > sno:  # sn later than sno so out of order escrow
                # escrow out-of-order event
                self.escrowOOEvent(serder=serder, seqner=seqner, diger=diger)
                raise OutOfOrderError("Out-of-order event={}.".format(ked))
            elif sn == sno:  # new inorder event
                tever.update(serder=serder, seqner=seqner, diger=diger, bigers=wigers)

                if not self.regk or self.regk != regk:
                    # witness style backers will need to send receipts so lets queue them up for now
                    # actually, lets not because the Kevery has no idea what to do with them!
                    # self.cues.append(dict(kin="receipt", serder=serder))
                    pass
            else:  # duplicitious
                raise LikelyDuplicitousError("Likely Duplicitous event={} with sn {}.".format(ked, sn))


    def processQuery(self, serder, source=None, sigers=None, cigars=None):
        """ Process TEL query event message (qry)

        Process query mode replay message for collective or single element query.
        Will cue response message with kin of "replay".  Assume promiscuous mode for now.

        Parameters:
            serder (Serder): is query message serder
            source (qb64): identifier prefix of querier
            sigers (list): Siger instances of attached controller indexed sigs
            cigars (list): Siger instances of non-transferable signatures

        """
        ked = serder.ked

        ilk = ked["t"]
        route = ked["r"]
        qry = ked["q"]

        # do signature validation and replay attack prevention logic here
        # src, dt, route

        if route == "tels":
            mgmt = qry["ri"]
            vcpre = qry["i"]
            vck = nsKey([mgmt, vcpre])

            cloner = self.reger.clonePreIter(pre=mgmt, fn=0)  # create iterator at 0
            msgs = bytearray()  # outgoing messages
            for msg in cloner:
                msgs.extend(msg)

            cloner = self.reger.clonePreIter(pre=vck, fn=0)  # create iterator at 0
            for msg in cloner:
                msgs.extend(msg)

            if msgs:
                self.cues.append(dict(kin="replay", dest=source, msgs=msgs))
        else:
            raise ValidationError("invalid query message {} for evt = {}".format(ilk, ked))

    @staticmethod
    def registryKey(serder):
        """  Utility method to extract registry key from any type of TEL serder

        Parameters:
            serder (Serder): event messate

        Returns:
            str: qb64 regsitry identifier
        """
        ilk = serder.ked["t"]

        if ilk in (Ilks.vcp, Ilks.vrt):
            return serder.pre
        elif ilk in (Ilks.iss, Ilks.rev):
            return serder.ked["ri"]
        elif ilk in (Ilks.bis, Ilks.brv):
            rega = serder.ked["ra"]
            return rega["i"]
        else:
            raise ValidationError("invalid ilk {} for tevery event = {}".format(ilk, serder.ked))


    def escrowOOEvent(self, serder, seqner, diger):
        """ Escrow out-of-order TEL events.

        Saves the serialized event, anchor and event digest in escrow for any
        event that is received out of order.

        Examples include registry rotation events, credential issuance event
         received before the registry inception event or a credential revocation
         event received before the issuance event.

        Parameters:
            serder (Serder): serder of event message
            seqner (Seqner): sequence number of anchoring TEL event
            diger (Diger) digest of anchoring TEL event


        """
        key = dgKey(serder.preb, serder.digb)
        self.reger.putTvt(key, serder.raw)
        sealet = seqner.qb64b + diger.qb64b
        self.reger.putAnc(key, sealet)
        self.reger.putOot(snKey(serder.preb, serder.sn), serder.digb)
        logger.info("Tever state: Escrowed our of order TEL event "
                    "event = %s\n", serder.ked)


    def processEscrows(self):
        """ Loop through escrows and process and events that may now be finalized """

        try:
            self.processEscrowAnchorless()
            self.processEscrowOutOfOrders()

        except Exception as ex:  # log diagnostics errors etc
            if logger.isEnabledFor(logging.DEBUG):
                logger.exception("Tevery escrow process error: %s\n", ex.args[0])
            else:
                logger.error("Tevery escrow process error: %s\n", ex.args[0])

    def processEscrowOutOfOrders(self):
        """ Loop through out of order escrow:

         Process out of order events in the following way:
           1. loop over event digests saved in oots
           2. deserialize event out of tvts
           3. read anchor information out of .ancs
           4. perform process event
           5. Remove event digest from oots if processed successfully or a non-out-of-order event occurs.

        """
        for (pre, snb, digb) in self.reger.getOotItemIter():
            print("oot-tel-event", pre)


    def processEscrowAnchorless(self):
        """ Process escrow of TEL events received before the anchoring KEL event.

        Process anchorless events in the following way:
           1. loop over event digests saved in taes
           2. deserialize event out of tvts
           3. load backer signatures out of tibs
           4. read anchor information out of ancs
           5. perform process event
           6. Remove event digest from oots if processed successfully or a non-anchorless event occurs.

        """
        for (pre, snb, digb) in self.reger.getTaeItemIter():
            sn = int(snb, 16)
            try:
                dgkey = dgKey(pre, digb)
                traw = self.reger.getTvt(dgkey)
                if traw is None:
                    # no event so raise ValidationError which unescrows below
                    logger.info("Tevery unescrow error: Missing event at."
                                "dig = %s\n", bytes(digb))

                    raise ValidationError("Missing escrowed evt at dig = {}."
                                          "".format(bytes(digb)))

                tserder = Serder(raw=bytes(traw))  # escrowed event

                bigers = None
                if tibs := self.reger.getTibs(key=dgkey):
                    bigers = [coring.Siger(qb64b=tib) for tib in tibs]

                couple = self.reger.getAnc(dgkey)
                if couple is None:
                    logger.info("Tevery unescrow error: Missing anchor at."
                                "dig = %s\n", bytes(digb))

                    raise ValidationError("Missing escrowed anchor at dig = {}."
                                          "".format(bytes(digb)))
                ancb = bytearray(couple)
                seqner = coring.Seqner(qb64b=ancb, strip=True)
                diger = coring.Diger(qb64b=ancb, strip=True)

                self.processEvent(serder=tserder, seqner=seqner, diger=diger, wigers=bigers)

            except MissingAnchorError as ex:
                # still waiting on missing prior event to validate
                if logger.isEnabledFor(logging.DEBUG):
                    logger.exception("Tevery unescrow failed: %s\n", ex.args[0])
                else:
                    logger.error("Tevery unescrow failed: %s\n", ex.args[0])

            except Exception as ex:  # log diagnostics errors etc
                # error other than out of order so remove from OO escrow
                self.reger.delTae(snKey(pre, sn))  # removes one escrow at key val
                if logger.isEnabledFor(logging.DEBUG):
                    logger.exception("Tevery unescrowed: %s\n", ex.args[0])
                else:
                    logger.error("Tevery unescrowed: %s\n", ex.args[0])

            else:  # unescrow succeeded, remove from escrow
                # We don't remove all escrows at pre,sn because some might be
                # duplicitous so we process remaining escrows in spite of found
                # valid event escrow.
                self.reger.delTae(snKey(pre, sn))  # removes from escrow
                logger.info("Tevery unescrow succeeded in valid event: "
                            "event=\n%s\n", json.dumps(tserder.ked, indent=1))
