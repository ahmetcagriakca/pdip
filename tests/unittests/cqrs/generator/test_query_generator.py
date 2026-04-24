"""Unit tests for ``pdip.cqrs.generator.query_generator.QueryGenerator``.

``QueryGenerator`` is a template-emitter: for every call to ``generate``
it asks its ``FolderManager`` to prepare a target folder and then tells
its ``FileManager`` to write seven files (Request, Dto, Response, Query,
Specifications, Mapping, QueryHandler) whose contents change based on
the ``QueryGenerateConfig`` flags (``is_list`` / ``has_paging``) and on
the injected ``DaoGenerateConfig`` (``name`` / ``namespace``).

The tests mock both managers at the boundary, drive ``generate`` with
different configs, and assert on the captured ``create_file`` kwargs so
that every branch of the emitter is pinned to a concrete behaviour.

No ``Pdi()`` boot, no real filesystem, no network — ADR-0026 compliant.
"""

from unittest import TestCase
from unittest.mock import MagicMock

from pdip.cqrs.generator.domain.dao_generate_config import DaoGenerateConfig
from pdip.cqrs.generator.domain.query_generate_config import QueryGenerateConfig
from pdip.cqrs.generator.query_generator import QueryGenerator


# ---------------------------------------------------------------------------
# Fixture factories
# ---------------------------------------------------------------------------


def _build_dao(name: str = "UserDao",
               namespace: str = "from infra.daos.UserDao import UserDao") -> DaoGenerateConfig:
    return DaoGenerateConfig(name=name, namespace=namespace)


def _build_config(name: str = "GetUser",
                  domain: str = "users",
                  base_directory: str = "application/services",
                  is_list: bool = True,
                  has_paging: bool = True,
                  dao: DaoGenerateConfig = None) -> QueryGenerateConfig:
    return QueryGenerateConfig(
        base_directory=base_directory,
        domain=domain,
        name=name,
        dao=dao if dao is not None else _build_dao(),
        is_list=is_list,
        has_paging=has_paging,
    )


def _build_generator():
    """Return a ``QueryGenerator`` wired with mock collaborators.

    The returned tuple exposes the mocks so each test can inspect the
    exact arguments passed to ``file_manager.create_file`` and
    ``folder_manager.start_copy``."""
    file_manager = MagicMock()
    folder_manager = MagicMock()
    application_config = MagicMock()
    module_finder = MagicMock()
    generator = QueryGenerator(
        application_config=application_config,
        module_finder=module_finder,
        folder_manager=folder_manager,
        file_manager=file_manager,
    )
    return generator, file_manager, folder_manager, application_config, module_finder


def _files_by_name(file_manager_mock) -> dict:
    """Map ``file_name`` -> captured ``create_file`` kwargs."""
    captured = {}
    for call in file_manager_mock.create_file.call_args_list:
        kwargs = call.kwargs
        captured[kwargs["file_name"]] = kwargs
    return captured


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


class QueryGeneratorStoresCollaborators(TestCase):
    def test_init_retains_all_four_collaborators_as_attributes(self):
        application_config = MagicMock()
        module_finder = MagicMock()
        folder_manager = MagicMock()
        file_manager = MagicMock()

        generator = QueryGenerator(
            application_config=application_config,
            module_finder=module_finder,
            folder_manager=folder_manager,
            file_manager=file_manager,
        )

        self.assertIs(generator.application_config, application_config)
        self.assertIs(generator.module_finder, module_finder)
        self.assertIs(generator.folder_manager, folder_manager)
        self.assertIs(generator.file_manager, file_manager)


# ---------------------------------------------------------------------------
# generate() — orchestration
# ---------------------------------------------------------------------------


class GenerateOrchestratesFolderAndFileEmission(TestCase):
    def test_generate_calls_start_copy_with_joined_query_folder_path(self):
        generator, _file_manager, folder_manager, _ac, _mf = _build_generator()
        config = _build_config(
            base_directory="app/services",
            domain="orders",
            name="GetOrder",
        )

        generator.generate(config)

        folder_manager.start_copy.assert_called_once_with("app/services/orders/GetOrder")

    def test_generate_emits_exactly_seven_files_per_query(self):
        generator, file_manager, _fm, _ac, _mf = _build_generator()

        generator.generate(_build_config())

        self.assertEqual(file_manager.create_file.call_count, 7)

    def test_generate_emits_the_seven_expected_file_names(self):
        generator, file_manager, _fm, _ac, _mf = _build_generator()
        config = _build_config(name="GetUser")

        generator.generate(config)

        files = _files_by_name(file_manager)
        self.assertEqual(
            set(files.keys()),
            {
                "GetUserRequest",
                "GetUserDto",
                "GetUserResponse",
                "GetUserQuery",
                "GetUserSpecifications",
                "GetUserMapping",
                "GetUserQueryHandler",
            },
        )

    def test_generate_routes_every_emitted_file_into_the_query_folder(self):
        generator, file_manager, _fm, _ac, _mf = _build_generator()
        config = _build_config(
            base_directory="svc", domain="users", name="GetUser",
        )

        generator.generate(config)

        folders = {call.kwargs["folder"] for call in file_manager.create_file.call_args_list}
        self.assertEqual(folders, {"svc/users/GetUser"})


# ---------------------------------------------------------------------------
# __create_query_file — Query class links Request and Response
# ---------------------------------------------------------------------------


class QueryFileWiresRequestAndResponse(TestCase):
    def test_query_file_declares_dataclass_query_parametrised_by_response(self):
        generator, file_manager, _fm, _ac, _mf = _build_generator()
        config = _build_config(name="GetUser", base_directory="svc", domain="users")

        generator.generate(config)

        query_content = _files_by_name(file_manager)["GetUserQuery"]["content"]
        self.assertIn("@dataclass", query_content)
        self.assertIn("class GetUserQuery(IQuery[GetUserResponse]):", query_content)
        self.assertIn("request: GetUserRequest = None", query_content)

    def test_query_file_imports_request_and_response_from_dotted_namespace(self):
        generator, file_manager, _fm, _ac, _mf = _build_generator()
        config = _build_config(name="GetUser", base_directory="svc", domain="users")

        generator.generate(config)

        query_content = _files_by_name(file_manager)["GetUserQuery"]["content"]
        self.assertIn(
            "from svc.users.GetUser.GetUserRequest import GetUserRequest",
            query_content,
        )
        self.assertIn(
            "from svc.users.GetUser.GetUserResponse import GetUserResponse",
            query_content,
        )


# ---------------------------------------------------------------------------
# __create_request_file — paging parent class switches on has_paging
# ---------------------------------------------------------------------------


class RequestFileReflectsPagingFlag(TestCase):
    def test_request_class_inherits_paging_and_orderby_when_has_paging(self):
        generator, file_manager, _fm, _ac, _mf = _build_generator()

        generator.generate(_build_config(name="GetUser", has_paging=True))

        request_content = _files_by_name(file_manager)["GetUserRequest"]["content"]
        self.assertIn(
            "class GetUserRequest(PagingParameter, OrderByParameter):",
            request_content,
        )

    def test_request_class_has_no_parent_list_when_not_has_paging(self):
        generator, file_manager, _fm, _ac, _mf = _build_generator()

        generator.generate(_build_config(name="GetUser", has_paging=False))

        request_content = _files_by_name(file_manager)["GetUserRequest"]["content"]
        self.assertIn("class GetUserRequest:", request_content)
        self.assertNotIn("PagingParameter", request_content)
        self.assertNotIn("OrderByParameter", request_content)

    def test_request_file_uses_requestclass_decorator(self):
        generator, file_manager, _fm, _ac, _mf = _build_generator()

        generator.generate(_build_config(name="GetUser"))

        request_content = _files_by_name(file_manager)["GetUserRequest"]["content"]
        self.assertIn("@requestclass", request_content)
        self.assertIn(
            "from domain.common.decorators.requestclass import requestclass",
            request_content,
        )


# ---------------------------------------------------------------------------
# __create_dto_file — shape does not depend on flags
# ---------------------------------------------------------------------------


class DtoFileIsStableAcrossFlags(TestCase):
    def test_dto_file_declares_empty_dtoclass_named_after_query(self):
        generator, file_manager, _fm, _ac, _mf = _build_generator()

        generator.generate(_build_config(name="GetUser"))

        dto_content = _files_by_name(file_manager)["GetUserDto"]["content"]
        self.assertIn("@dtoclass", dto_content)
        self.assertIn("class GetUserDto:", dto_content)
        self.assertIn(
            "from domain.common.decorators.dtoclass import dtoclass",
            dto_content,
        )


# ---------------------------------------------------------------------------
# __create_response_file — Data field shape depends on is_list / has_paging
# ---------------------------------------------------------------------------


class ResponseFileReflectsListAndPagingFlags(TestCase):
    def test_response_exposes_list_and_paging_metadata_when_list_and_paging(self):
        generator, file_manager, _fm, _ac, _mf = _build_generator()

        generator.generate(_build_config(name="GetUser", is_list=True, has_paging=True))

        response_content = _files_by_name(file_manager)["GetUserResponse"]["content"]
        self.assertIn("Data: List[GetUserDto] = None", response_content)
        self.assertIn("PageNumber: int = None", response_content)
        self.assertIn("PageSize: int = None", response_content)
        self.assertIn("Count: int = None", response_content)

    def test_response_exposes_list_without_paging_metadata_when_list_only(self):
        generator, file_manager, _fm, _ac, _mf = _build_generator()

        generator.generate(_build_config(name="GetUser", is_list=True, has_paging=False))

        response_content = _files_by_name(file_manager)["GetUserResponse"]["content"]
        self.assertIn("Data: List[GetUserDto] = None", response_content)
        self.assertNotIn("PageNumber", response_content)
        self.assertNotIn("PageSize", response_content)
        self.assertNotIn("Count: int", response_content)

    def test_response_exposes_single_dto_when_not_list(self):
        generator, file_manager, _fm, _ac, _mf = _build_generator()

        generator.generate(_build_config(name="GetUser", is_list=False, has_paging=False))

        response_content = _files_by_name(file_manager)["GetUserResponse"]["content"]
        self.assertIn("Data: GetUserDto = None", response_content)
        self.assertNotIn("List[GetUserDto]", response_content)

    def test_response_imports_dto_from_dotted_namespace(self):
        generator, file_manager, _fm, _ac, _mf = _build_generator()

        generator.generate(_build_config(name="GetUser", base_directory="svc", domain="users"))

        response_content = _files_by_name(file_manager)["GetUserResponse"]["content"]
        self.assertIn(
            "from svc.users.GetUser.GetUserDto import GetUserDto",
            response_content,
        )


# ---------------------------------------------------------------------------
# __create_specifications_file — constructor injection varies with has_paging
# ---------------------------------------------------------------------------


class SpecificationsFileInjectsPagingCollaboratorsConditionally(TestCase):
    def test_specifications_injects_paging_and_orderby_when_list_with_paging(self):
        generator, file_manager, _fm, _ac, _mf = _build_generator()
        dao = _build_dao(
            name="UserDao",
            namespace="from infra.daos.UserDao import UserDao",
        )

        generator.generate(_build_config(
            name="GetUser", is_list=True, has_paging=True, dao=dao,
        ))

        spec_content = _files_by_name(file_manager)["GetUserSpecifications"]["content"]
        self.assertIn(
            "from domain.common.specifications.OrderBySpecification import OrderBySpecification",
            spec_content,
        )
        self.assertIn(
            "from domain.common.specifications.PagingSpecification import PagingSpecification",
            spec_content,
        )
        self.assertIn("order_by_specification: OrderBySpecification,", spec_content)
        self.assertIn("paging_specification: PagingSpecification,", spec_content)
        self.assertIn("self.paging_specification = paging_specification", spec_content)
        self.assertIn("self.order_by_specification = order_by_specification", spec_content)

    def test_specifications_omits_paging_injection_when_not_has_paging(self):
        generator, file_manager, _fm, _ac, _mf = _build_generator()

        generator.generate(_build_config(name="GetUser", has_paging=False))

        spec_content = _files_by_name(file_manager)["GetUserSpecifications"]["content"]
        self.assertNotIn("OrderBySpecification", spec_content)
        self.assertNotIn("PagingSpecification", spec_content)
        self.assertNotIn("order_by_specification", spec_content)
        self.assertNotIn("paging_specification", spec_content)

    def test_specifications_embeds_ordering_and_paging_statements_when_has_paging(self):
        generator, file_manager, _fm, _ac, _mf = _build_generator()

        generator.generate(_build_config(name="GetUser", has_paging=True))

        spec_content = _files_by_name(file_manager)["GetUserSpecifications"]["content"]
        self.assertIn("data_query = data_query.order_by(order_by)", spec_content)
        self.assertIn("data_query = data_query.limit(page_size)", spec_content)
        self.assertIn("data_query = data_query.offset(offset)", spec_content)

    def test_specifications_skips_ordering_and_paging_statements_when_not_has_paging(self):
        generator, file_manager, _fm, _ac, _mf = _build_generator()

        generator.generate(_build_config(name="GetUser", has_paging=False))

        spec_content = _files_by_name(file_manager)["GetUserSpecifications"]["content"]
        self.assertNotIn("order_by_specification.specify", spec_content)
        self.assertNotIn("limit(page_size)", spec_content)
        self.assertNotIn(".offset(offset)", spec_content)

    def test_specifications_embeds_dao_namespace_and_resolves_repository_for_dao(self):
        generator, file_manager, _fm, _ac, _mf = _build_generator()
        dao = _build_dao(
            name="OrderDao",
            namespace="from infra.daos.OrderDao import OrderDao",
        )

        generator.generate(_build_config(name="GetOrder", dao=dao))

        spec_content = _files_by_name(file_manager)["GetOrderSpecifications"]["content"]
        self.assertIn("from infra.daos.OrderDao import OrderDao", spec_content)
        self.assertIn("repository = self.repository_provider.get(OrderDao)", spec_content)

    def test_specifications_defines_count_method_delegating_to_private_specified_query(self):
        generator, file_manager, _fm, _ac, _mf = _build_generator()

        generator.generate(_build_config(name="GetUser"))

        spec_content = _files_by_name(file_manager)["GetUserSpecifications"]["content"]
        self.assertIn("def count(self, query: GetUserQuery) -> Query:", spec_content)
        self.assertIn(
            "return self.__specified_query(query=query).count()",
            spec_content,
        )


# ---------------------------------------------------------------------------
# __create_mapping_file — uses dao name / namespace and query name
# ---------------------------------------------------------------------------


class MappingFileBindsDtoAndDao(TestCase):
    def test_mapping_declares_to_dto_and_to_dtos_typed_on_dao_and_dto(self):
        generator, file_manager, _fm, _ac, _mf = _build_generator()
        dao = _build_dao(
            name="UserDao",
            namespace="from infra.daos.UserDao import UserDao",
        )

        generator.generate(_build_config(name="GetUser", dao=dao))

        mapping_content = _files_by_name(file_manager)["GetUserMapping"]["content"]
        self.assertIn("class GetUserMapping:", mapping_content)
        self.assertIn(
            "def to_dto(cls, entity: UserDao) -> GetUserDto:",
            mapping_content,
        )
        self.assertIn(
            "def to_dtos(cls, entities: List[UserDao]) -> List[GetUserDto]:",
            mapping_content,
        )
        self.assertIn("from infra.daos.UserDao import UserDao", mapping_content)


# ---------------------------------------------------------------------------
# __create_query_handler_file — paging / list branches
# ---------------------------------------------------------------------------


class QueryHandlerFileReflectsListAndPagingFlags(TestCase):
    def test_handler_populates_count_pagenumber_pagesize_when_has_paging(self):
        generator, file_manager, _fm, _ac, _mf = _build_generator()

        generator.generate(_build_config(name="GetUser", has_paging=True, is_list=True))

        handler_content = _files_by_name(file_manager)["GetUserQueryHandler"]["content"]
        self.assertIn("result.Count = self.specifications.count(query=query)", handler_content)
        self.assertIn("result.PageNumber = query.request.PageNumber", handler_content)
        self.assertIn("result.PageSize = query.request.PageSize", handler_content)

    def test_handler_omits_count_and_paging_assignments_when_not_has_paging(self):
        generator, file_manager, _fm, _ac, _mf = _build_generator()

        generator.generate(_build_config(name="GetUser", has_paging=False, is_list=True))

        handler_content = _files_by_name(file_manager)["GetUserQueryHandler"]["content"]
        self.assertNotIn("result.Count", handler_content)
        self.assertNotIn("result.PageNumber", handler_content)
        self.assertNotIn("result.PageSize", handler_content)

    def test_handler_calls_to_dtos_when_is_list(self):
        generator, file_manager, _fm, _ac, _mf = _build_generator()

        generator.generate(_build_config(name="GetUser", is_list=True, has_paging=False))

        handler_content = _files_by_name(file_manager)["GetUserQueryHandler"]["content"]
        self.assertIn("result.Data = GetUserMapping.to_dtos(data_query)", handler_content)
        self.assertNotIn("GetUserMapping.to_dto(data_query)", handler_content)

    def test_handler_calls_to_dto_when_not_is_list(self):
        generator, file_manager, _fm, _ac, _mf = _build_generator()

        generator.generate(_build_config(name="GetUser", is_list=False, has_paging=False))

        handler_content = _files_by_name(file_manager)["GetUserQueryHandler"]["content"]
        self.assertIn("result.Data = GetUserMapping.to_dto(data_query)", handler_content)
        self.assertNotIn("to_dtos(data_query)", handler_content)

    def test_handler_declares_injected_specifications_and_iqueryhandler_base(self):
        generator, file_manager, _fm, _ac, _mf = _build_generator()

        generator.generate(_build_config(name="GetUser"))

        handler_content = _files_by_name(file_manager)["GetUserQueryHandler"]["content"]
        self.assertIn(
            "class GetUserQueryHandler(IQueryHandler[GetUserQuery], IScoped):",
            handler_content,
        )
        self.assertIn("specifications: GetUserSpecifications", handler_content)
        self.assertIn("self.specifications = specifications", handler_content)
        self.assertIn(
            "def handle(self, query: GetUserQuery) -> GetUserResponse:",
            handler_content,
        )

    def test_handler_imports_siblings_from_dotted_namespace(self):
        generator, file_manager, _fm, _ac, _mf = _build_generator()

        generator.generate(_build_config(name="GetUser", base_directory="svc", domain="users"))

        handler_content = _files_by_name(file_manager)["GetUserQueryHandler"]["content"]
        for expected_import in (
            "from svc.users.GetUser.GetUserMapping import GetUserMapping",
            "from svc.users.GetUser.GetUserQuery import GetUserQuery",
            "from svc.users.GetUser.GetUserResponse import GetUserResponse",
            "from svc.users.GetUser.GetUserSpecifications import GetUserSpecifications",
        ):
            self.assertIn(expected_import, handler_content)
