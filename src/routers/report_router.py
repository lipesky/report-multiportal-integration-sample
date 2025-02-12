from functools import lru_cache
from tempfile import NamedTemporaryFile
from fastapi import APIRouter, Depends, Query
from typing import Annotated, Any, List

from fastapi.responses import FileResponse
from src.routers.validators import validate_valid_jwt
from src.service.report_service import ReportService, get_report_service

router = APIRouter(
    prefix='/report'
)

@router.get("/capacity-xlsx", dependencies=[Depends(validate_valid_jwt)])
async def capacity(
    reportService: Annotated[ReportService, Depends(get_report_service)], 
    # startDate: Annotated[str | None, Query()] = None,
    # endDate: Annotated[str | None, Query()] = None,
    date: Annotated[str | None, Query()] = None,
    comercial_id: Annotated[str | None, Query()] = None,
) -> List[Any]:
    (book, title) = await reportService.occupation_report_xlsx(date, comercial_id)
    with NamedTemporaryFile(delete=False, suffix='.xlsx') as file:
        book.save(file)
        file.seek(0)
        return FileResponse(file.name, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',filename=title)

@router.get("/capacity")#, dependencies=[Depends(validate_valid_jwt)])
async def capacity(
    reportService: Annotated[ReportService, Depends(get_report_service)], 
    # startDate: Annotated[str | None, Query()] = None,
    # endDate: Annotated[str | None, Query()] = None,
    date: Annotated[str | None, Query()] = None,
    comercial_id: Annotated[str | None, Query()] = None,
) -> List[Any]:
    return await reportService.build_data_for_ocuppation_report(date, comercial_id)