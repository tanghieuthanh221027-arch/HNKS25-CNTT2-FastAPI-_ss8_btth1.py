from typing import Literal , Any
from fastapi import FastAPI, HTTPException, Query, status , Request
from pydantic import BaseModel, Field
from datetime import datetime , date
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

app = FastAPI()

carriers = [
    {
        "id": 1,
        "code": "GHN",
        "name": "Giao Hang Nhanh",
        "max_weight_capacity": 5000,
        "status": "ACTIVE",
    },
    {
        "id": 2,
        "code": "GHTK",
        "name": "Giao Hang Tiet Kiem",
        "max_weight_capacity": 3000,
        "status": "ACTIVE",
    },
    {
        "id": 3,
        "code": "VTP",
        "name": "Viettel Post",
        "max_weight_capacity": 10000,
        "status": "SUSPENDED",
    },
]

shipments = [
    {
        "id": 1,
        "carrier_id": 1,
        "order_reference": "ORD-2026-001",
        "total_weight": 4200,
        "dispatch_date": "2026-07-01",
        "shift": "MORNING",
    }
]


class CarrierCreate(BaseModel):
    code: str
    name: str = Field(min_length=3)
    max_weight_capacity: int = Field(gt=0)
    status: Literal["ACTIVE", "INACTIVE", "SUSPENDED"]


class ShipmentCreate(BaseModel):
    carrier_id: int
    order_reference: str
    total_weight: int = Field(gt=0)
    dispatch_date: date
    shift: Literal["MORNING", "AFTERNOON", "NIGHT"]


@app.post("/carriers", status_code=status.HTTP_201_CREATED)
def create_carrier(carrier: CarrierCreate):
    for item in carriers:
        if item["code"].lower() == carrier.code.lower():
            raise HTTPException(
                status_code=400,
                detail="Carrier code already exists",
            )

    new_carrier = carrier.model_dump()
    new_carrier["id"] = len(carriers) + 1
    carriers.append(new_carrier)

    return response_json(
        status_code=201,
        message="Carrier created successfully",
        data=new_carrier,
        error=None,
        path="/carriers",
    )


@app.get("/carriers")
def get_carriers(
    keyword: str | None = Query(None),
    status_filter: Literal["ACTIVE", "INACTIVE", "SUSPENDED"] | None = Query(
        None,
        alias="status",
    ),
    min_weight: int | None = Query(None, ge=1),
):
    result = carriers

    if keyword:
        keyword = keyword.lower()
        result = [
            item
            for item in result
            if keyword in item["code"].lower()
            or keyword in item["name"].lower()
        ]

    if status_filter:
        result = [
            item
            for item in result
            if item["status"] == status_filter
        ]

    if min_weight is not None:
        result = [
            item
            for item in result
            if item["max_weight_capacity"] >= min_weight
        ]

    return response_json(
        status_code=200,
        message="Carrier list",
        data=result,
        error=None,
        path="/carriers",
    )


@app.get("/carriers/{carrier_id}")
def get_carrier(carrier_id: int):
    carrier = next(
        (item for item in carriers if item["id"] == carrier_id),
        None,
    )

    if carrier is None:
        raise HTTPException(
            status_code=404,
            detail="Carrier not found",
        )

    return response_json(
        status_code=200,
        message="Carrier detail",
        data=carrier,
        error=None,
        path=f"/carriers/{carrier_id}",
    )


@app.put("/carriers/{carrier_id}")
def update_carrier(
    carrier_id: int,
    carrier: CarrierCreate,
):
    current = next(
        (item for item in carriers if item["id"] == carrier_id),
        None,
    )

    if current is None:
        raise HTTPException(
            status_code=404,
            detail="Carrier not found",
        )

    for item in carriers:
        if (
            item["id"] != carrier_id
            and item["code"].lower() == carrier.code.lower()
        ):
            raise HTTPException(
                status_code=400,
                detail="Carrier code already exists",
            )

    current.update(carrier.model_dump())

    return response_json(
        status_code=200,
        message="Carrier updated successfully",
        data=current,
        error=None,
        path=f"/carriers/{carrier_id}",
    )


@app.delete("/carriers/{carrier_id}")
def delete_carrier(carrier_id: int):
    carrier = next(
        (item for item in carriers if item["id"] == carrier_id),
        None,
    )

    if carrier is None:
        raise HTTPException(
            status_code=404,
            detail="Carrier not found",
        )

    carriers.remove(carrier)

    return response_json(
        status_code=200,
        message="Carrier deleted successfully",
        data=None,
        error=None,
        path=f"/carriers/{carrier_id}",
    )


@app.post("/shipments", status_code=status.HTTP_201_CREATED)
def create_shipment(shipment: ShipmentCreate):
    carrier = next(
        (
            item
            for item in carriers
            if item["id"] == shipment.carrier_id
        ),
        None,
    )

    if carrier is None:
        raise HTTPException(
            status_code=404,
            detail="Carrier not found",
        )

    if carrier["status"] != "ACTIVE":
        raise HTTPException(
            status_code=400,
            detail="Carrier is not active",
        )

    if shipment.total_weight > carrier["max_weight_capacity"]:
        raise HTTPException(
            status_code=400,
            detail="Shipment exceeds carrier capacity",
        )

    for item in shipments:
        if (
            item["carrier_id"] == shipment.carrier_id
            and item["dispatch_date"] == str(shipment.dispatch_date)
            and item["shift"] == shipment.shift
        ):
            raise HTTPException(
                status_code=400,
                detail="Carrier already has a shipment in this shift",
            )

    new_shipment = shipment.model_dump()
    new_shipment["id"] = len(shipments) + 1
    new_shipment["dispatch_date"] = str(
        new_shipment["dispatch_date"]
    )

    shipments.append(new_shipment)

    return response_json(
        status_code=201,
        message="Shipment created successfully",
        data=new_shipment,
        error=None,
        path="/shipments",
    )


@app.get("/shipments")
def get_shipments():
    return response_json(
        status_code=200,
        message="Shipment list",
        data=shipments,
        error=None,
        path="/shipments",
    )

def response_json(
    status_code: int,
    message: str,
    data: Any,
    error: Any,
    path: str,
):
    return JSONResponse(
        status_code=status_code,
        content={
            "statusCode": status_code,
            "message": message,
            "data": data,
            "error": error,
            "timestamp": datetime.now().isoformat(),
            "path": path,
        },
    )


@app.exception_handler(RequestValidationError)
def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    return response_json(
        status_code=422,
        message="Validation Error",
        data=None,
        error=exc.errors(),
        path=request.url.path,
    )

@app.exception_handler(HTTPException)
def http_exception_handler(
    request: Request,
    exc: HTTPException,
):
    return response_json(
        status_code=exc.status_code,
        message=exc.detail,
        data=None,
        error=exc.detail,
        path=request.url.path,
    )

@app.exception_handler(Exception)
def server_exception_handler(
    request: Request,
    exc: Exception,
):
    return response_json(
        status_code=500,
        message="Internal Server Error",
        data=None,
        error=str(exc),
        path=request.url.path,
    )