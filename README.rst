================================
Mux video streaming LTI producer
================================

This is a pluggable LTI producer to stream videos hosted on `Mux <https://mux.com>`__. It must be integrated with the `Django LTI producer server <https://github.com/strata-kk/lti-producer>`__.


Installation
============

We assume that you have a working installation of the LTI producer. Install the Django reusable app from source::

    pip install -e git+https://github.com/strata-kk/mux-videos-lti-producer

Then, add the following settings to your Django project::

    LTI_PRODUCER_URLS = {
        "mux": "muxltiproducer.urls",
    }
    LTI_LAUNCH_VIEWS = {
        "mux": "mux:launch",
    }

You must also define the required settings; see "Configuration" below. Then, run your LTI producer.

LMS integration
===============

The Mux LTI application expects the following custom parameters to be sent along with every launch request:

- ``custom_app=mux``: this serves to identify the LTI app to which the LTI producer will forward requests.
- ``custom_video_id=the-mux-asset-id``: when undefined, a message will be displayed to tell the instructor to pick a video ID from the instructor tab.

Configuration
=============

The behaviour of this application is defined by the following Django settings.

``MUX_TOKEN_ID`` (required)
---------------------------

Default: ``""`` (empty string)

Mux API token ID generated for your project. New tokens can be generated in your dashboard: https://dashboard.mux.com/settings/access-tokens

``MUX_TOKEN_SECRET`` (required)
-------------------------------

Default: ``""`` (empty string)

Mux API token secret corresponding to the ``MUX_TOKEN_ID`` (see above).

``MUX_ENABLE_SIGNED_PLAYBACK``
------------------------------

Default: ``True``

When ``True``, video asset playback urls are generated on-the-fly for every page load. These urls are valid for a limited time, defined by ``MUX_SIGNED_URL_EXPIRY_SECONDS``. This prevents the sharing of video urls for too long. Set to ``False`` to upload video assets with a public playback policy. Public assets will be forever playable from a single url.

If ``True``, the following settings must be defined: ``MUX_SIGNING_KEY_ID``, ``MUX_SIGNING_PRIVATE_KEY``. 

``MUX_SIGNING_KEY_ID``
----------------------

Default: ``""`` (empty string)

When signed playback is enabled (see ``MUX_ENABLE_SIGNED_PLAYBACK`` above), this is the ID of the signing key that will be used to sign playback urls. To generate this signing keys:

1. Run::

    ./manage.py mux_signing_key

2. Use the values from the 'id' and 'private_key' fields to define ``MUX_SIGNING_KEY_ID`` and ``MUX_SIGNING_PRIVATE_KEY``.

When you create a signing key, you should remember to also create a playback restriction for your environment: https://docs.mux.com/api-reference/video#operation/create-playback-restriction

For more information about signing keys and playback restrictions, see the docs: https://docs.mux.com/api-reference/video#operation/create-url-signing-key


``MUX_SIGNING_PRIVATE_KEY``
---------------------------

Default: ``""`` (empty string)

Private key of the signing key defined by ``MUX_SIGNING_KEY_ID`` (see above).

``MUX_SIGNED_URL_EXPIRY_SECONDS``
---------------------------------

Default: ``604800`` (7 days)

Validity duration of signed Mux assets urls, in seconds. Videos will remain playable without reloading the browser tab for that long.

``MUX_ASSET_INSTRUCTOR_ACCESS_LIMITED_TO``
------------------------------------------

Default: ``None``

Limit the access of assets to instructors from the same organization, course or course run.

- ``None``: grant access to all assets to all instructors.
- ``"RUN"``: display only assets from the same course run.
- ``"COURSE"``: display only assets from the same course.
- ``"ORGANIZATION"``: display only assets from the same organization.

``MUX_UPLOAD_URL_VALIDITY_SECONDS``
-----------------------------------

Default: ``172800`` (2 days)

Validity duration of upload urls, in seconds. Uploads that last longer will fail.

``MUX_CAN_INSTRUCTORS_DELETE_ASSETS``
-------------------------------------

Default: ``True``

Set to False to prevent instructors from deleting assets from the frontend.

``MUX_WEBHOOK_SIGNING_SECRET``
------------------------------

Default: ``""``

Mux is able to send notifications to your app at every step of the asset creation process. This means that we do not have to frequently poll the Mux API for updates. To enable this feature, you should create a webhook from the Mux UI:

1. Go to https://dashboard.mux.com/settings/webhooks
2. Create a webhook that will point to your LTI producer: http(s)://yourltihost/mux/callback
3. Copy the generated signing secret and use it in your project settings as ``MUX_WEBHOOK_SIGNING_SECRET``.

In development it is recommended to use `Ngrok <https://ngrok.com/>`__ to capture callback events.

Notes
=====

Asynchronous task processing
----------------------------

Several parts of this LTI producer are implemented as asynchronous functions, for reasons of performance and reliability. However, in some cases it may be necessary to run manual commands to fetch some information from the Mux API. For instance, in development it may be difficult to receive callbacks from the Mux webhooks (see above). Thus, after uploading a video asset, users will face the message: "Video successfully uploaded. Waiting for processing...". This message will only be updated after the "synchronize" cron task has run, and that's only at the top of every hour. To run this task immediately, you should run the "mux_sync" management task. With the development producer, that would be::

    ./standalone/producer/manage.py mux_sync

Uploading subtitles
-------------------

Sending subtitle files to Mux implies that we make the files available at a public url. To do so, we make use of Django's ``DefaultStorage.url`` function. This works great in production, but in development Mux will not be able to fetch the files. This means that they will appear as being correctly uploaded, but they will not be available during playback.

Also, all uploaded files will be stored in a "mux/subtitles" subfolder of the media folder (indicated by the ``MEDIA_ROOT`` setting). Subtitle files are useless after they are transfered to Mux. They will be automatically deleted after an hour (see "asynchronous task processing" above).

Development
===========

::

    pip install -e .[dev]
    make test

Upgrade vendor javascript requirements::

    npm update
    npm install # this should automatically run 'gulp'

License
=======

The code in this repository is licensed under version 3 of the AGPL unless otherwise noted. See the LICENSE.txt file for details.
