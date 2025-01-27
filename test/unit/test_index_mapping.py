from tracardi.context import Context, ServerContext, get_context
from tracardi.config import tracardi

namespace = "tenant"
with ServerContext(Context(production=False, tenant=namespace)):

    from datetime import datetime

    import pytest

    from tracardi.domain.storage.index_mapping import IndexMapping
    from tracardi.domain.user import User
    from tracardi.service.storage.index import Index

    admin = User(id="1", password="pass", full_name="test", email="none", roles=['admin'])
    tenant = get_context().tenant

    mapping_mock = {
        "tracardi-event-2022-2": {
            "mappings": {
                "dynamic": "false",
                "properties": {
                    "aux": {
                        "type": "object",
                        "dynamic": "true"
                    },
                    "id": {
                        "type": "keyword"
                    },
                    "metadata": {
                        "properties": {
                            "debugged": {
                                "type": "boolean"
                            },
                            "processed_by": {
                                "properties": {
                                    "rules": {
                                        "type": "keyword"
                                    },
                                    "third_party": {
                                        "type": "keyword"
                                    }
                                }
                            },
                            "profile_less": {
                                "type": "boolean"
                            },
                            "status": {
                                "type": "keyword",
                                "null_value": "NULL"
                            },
                            "aux": {
                                "type": "flattened"
                            },
                            "time": {
                                "properties": {
                                    "insert": {
                                        "type": "date"
                                    }
                                }
                            }
                        }
                    },
                    "profile": {
                        "properties": {
                            "id": {
                                "type": "keyword"
                            }
                        }
                    },
                    "properties": {
                        "type": "object",
                        "dynamic": "true"
                    },
                    "session": {
                        "properties": {
                            "duration": {
                                "type": "float"
                            },
                            "id": {
                                "type": "keyword"
                            },
                            "start": {
                                "type": "date"
                            }
                        }
                    },
                    "source": {
                        "properties": {
                            "id": {
                                "type": "keyword"
                            }
                        }
                    },
                    "tags": {
                        "properties": {
                            "count": {
                                "type": "double"
                            },
                            "values": {
                                "type": "keyword"
                            }
                        }
                    },
                    "type": {
                        "type": "keyword",
                        "null_value": "NULL"
                    }
                }
            }
        }
    }


    def test_index_mapping():
        im = IndexMapping(mapping_mock)

        assert im.get_field_names() == ['aux', 'id', 'metadata.debugged', 'metadata.processed_by.rules',
                                        'metadata.processed_by.third_party', 'metadata.profile_less', 'metadata.status',
                                        'metadata.aux', 'metadata.time.insert', 'profile.id', 'properties',
                                        'session.duration', 'session.id', 'session.start', 'source.id', 'tags.count',
                                        'tags.values', 'type']


    def test_index_prefixing():
        with ServerContext(Context(production=False, tenant=namespace)):
            index = Index(multi_index=False, index="index-name", mapping=mapping_mock)
            alias = index.get_index_alias()
            assert alias == f"{tenant}.{index.index}"


    def test_write_index():
        with ServerContext(Context(production=False, tenant=namespace)):
            index = Index(multi_index=True, static=False, index="index-name", mapping=mapping_mock)
            write_index = index.get_write_index()
            alias = index.get_index_alias()

            date = datetime.now()
            assert write_index == f"{tracardi.version.get_version_prefix()}.{tenant}.index-name-{date.year}-{date.month}"
            assert alias == f"{tenant}.index-name"
            with ServerContext(Context(production=True, user=admin, tenant=namespace)):
                write_index = index.get_write_index()
                alias = index.get_index_alias()

                assert write_index == f"prod-{tracardi.version.get_version_prefix()}.{tenant}.index-name-{date.year}-{date.month}"
                assert alias == f"prod-{tenant}.index-name"


    def test_static_index():
        with ServerContext(Context(production=False, tenant=namespace)):
            index = Index(multi_index=False, static=True, index="index-name", mapping=mapping_mock)
            write_index = index.get_write_index()
            alias = index.get_index_alias()

            assert write_index == f"static-{tracardi.version.get_version_prefix()}.{tenant}.index-name"
            assert alias == f"static-{tenant}.index-name"


    def test_regular_index():
        with ServerContext(Context(production=False, tenant=namespace)):
            index = Index(multi_index=False, static=False, index="index-name", mapping=mapping_mock)
            write_index = index.get_write_index()
            alias = index.get_index_alias()

            assert write_index == f"{tracardi.version.get_version_prefix()}.{tenant}.index-name"
            assert alias == f"{tenant}.index-name"

            with ServerContext(Context(production=True, user=admin, tenant=namespace)):
                write_index = index.get_write_index()
                alias = index.get_index_alias()

                assert write_index == f"prod-{tracardi.version.get_version_prefix()}.{tenant}.index-name"
                assert alias == f"prod-{tenant}.index-name"


    def test_single_storage_index():
        with ServerContext(Context(production=False, tenant=namespace)):
            index = Index(multi_index=False, static=True, index="index-name", mapping=mapping_mock)
            write_index = index.get_single_storage_index()
            assert write_index == f"static-{tracardi.version.get_version_prefix()}.{tenant}.index-name"


    def test_multi_storage_index():
        with ServerContext(Context(production=False, tenant=namespace)):
            index = Index(multi_index=True, static=True, index="index-name", mapping=mapping_mock)
            write_index = index.get_current_multi_storage_index()
            date = datetime.now()
            assert write_index == f"static-{tracardi.version.get_version_prefix()}.{tenant}.index-name-{date.year}-{date.month}"

            with ServerContext(Context(production=True, user=admin, tenant=namespace)):
                index.static = False
                write_index = index.get_current_multi_storage_index()
                date = datetime.now()
                assert write_index == f"prod-{tracardi.version.get_version_prefix()}.{tenant}.index-name-{date.year}-{date.month}"


    def test_multi_storage_alias():
        with ServerContext(Context(production=False, tenant=namespace)):
            index = Index(multi_index=True, static=False, index="index-name", mapping=mapping_mock)
            write_index = index.get_multi_storage_alias()
            assert write_index == f"{tenant}.index-name"

            with ServerContext(Context(production=True, user=admin, tenant=namespace)):
                write_index = index.get_multi_storage_alias()
                assert write_index == f"prod-{tenant}.index-name"


    def test_template():
        with ServerContext(Context(production=False, tenant=namespace)):
            with pytest.raises(AssertionError):
                index = Index(multi_index=True, static=True, index="index-name", mapping=mapping_mock)
                template = index.get_prefixed_template_name()
                assert template == f"static-template.{tracardi.version.get_version_prefix()}.{tenant}.index-name"

            index = Index(multi_index=True, static=False, index="index-name", mapping=mapping_mock)
            template = index.get_prefixed_template_name()
            assert template == f"template.{tracardi.version.get_version_prefix()}.{tenant}.index-name"

            with ServerContext(Context(production=True, user=admin, tenant=namespace)):
                index = Index(multi_index=True, static=False, index="index-name", mapping=mapping_mock)
                template = index.get_prefixed_template_name()
                assert template == f"prod-template.{tracardi.version.get_version_prefix()}.{tenant}.index-name"

            with pytest.raises(AssertionError):
                index = Index(multi_index=False, static=False, index="index-name", mapping=mapping_mock)
                template = index.get_prefixed_template_name()
                assert template == f"template.{tracardi.version.get_version_prefix()}.{tenant}.index-name"


    def test_templated_index():
        version = tracardi.version.get_version_prefix()
        with ServerContext(Context(production=False, tenant=namespace)):
            with pytest.raises(AssertionError):
                index = Index(multi_index=True, static=True, index="index-name", mapping=mapping_mock)
                pattern = index.get_templated_index_pattern()

            index = Index(multi_index=True, static=False, index="index-name", mapping=mapping_mock)
            pattern = index.get_templated_index_pattern()
            assert pattern == f"{version}.{tenant}.index-name-*-*"

            with ServerContext(Context(production=True, user=admin, tenant=namespace)):
                index = Index(multi_index=True, static=False, index="index-name", mapping=mapping_mock)
                pattern = index.get_templated_index_pattern()

        assert pattern == f"prod-{version}.{tenant}.index-name-*-*"


    def test_prod_static():
        with ServerContext(Context(production=False, tenant=namespace)):
            index = Index(multi_index=False, static=True, index="index-name", mapping=mapping_mock)

            # Static is more important than production
            with ServerContext(Context(production=True, user=admin, tenant=namespace)):
                write_index = index.get_write_index()
                assert write_index == f"static-{tracardi.version.get_version_prefix()}.{tenant}.index-name"

                index.static = False
                write_index = index.get_write_index()
                assert write_index == f"prod-{tracardi.version.get_version_prefix()}.{tenant}.index-name"
