import os
from dotenv import load_dotenv
from fastapi import FastAPI, Body, HTTPException, status
from fastapi.responses import Response, JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field, EmailStr
from bson import ObjectId
from typing import Optional, List, Set, Union
import motor.motor_asyncio

load_dotenv()

app = FastAPI()
client = motor.motor_asyncio.AsyncIOMotorClient(os.environ["MONGODB_URL"])
db = client.GestionPaquetes

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

class PaqueteRemite(BaseModel):
    Nombre: str
    Telefono:int
    Fecha_envio:str
    Hora_envio:str

class PaqueteRecibe(BaseModel):
    Nombre: str
    Telefono:int
    Fecha_recibe:Union[str, None] = None 
    Hora_recibe:Union[str, None] = None 
    
class StatusPaquete(BaseModel):
    Pais: str
    direccion_envio: str
    codigo_postal: int
    Estado_paquete: str

class PaqueteModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    Remitente: Union[PaqueteRemite, None] = None
    Resecciona:Union[PaqueteRecibe, None] = None
    Paquete:Union[StatusPaquete, None] = None
    id_envio: str 


    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "Remitente":{
                    "Nombre": "Jonathan",
                    "Telefono":3123733895,
                    "Fecha_envio":"1/12/2022",
                    "Hora_envio":"5:18"
                },
                "Resecciona":{
                    "Nombre": " Sebastian",
                    "Telefono":3123454345
                },
                "Paquete":{
                    "Pais": "Colombia",
                    "direccion_envio": "Cll 12 #15-64",
                    "codigo_postal": 34435523,
                    "Estado_paquete": "Enviado"
                },
                "id_envio":"ENV-0001"

            }
        }


@app.get(
    "/all", response_description="Lista de envios", response_model=List[PaqueteModel]
)
async def lista_paquetes():
    Paquetes = await db["data_paquetes"].find().to_list(1000)
    return Paquetes


@app.get(
    "/{id}", response_description="Solicitar envio por id", response_model=PaqueteModel
)
async def show_paquete(id: str):
    if (paquete := await db["data_paquetes"].find_one({"id_envio": id})) is not None:
        return paquete
    raise HTTPException(status_code=404, detail=f"Envio con id: {id} no existe!")


@app.post("/newEnvio", response_description="Añadir un envio", response_model=PaqueteModel)
async def create_envio(Paquete: PaqueteModel = Body(...)):
    print(Paquete)
    Paquete = jsonable_encoder(Paquete)
    new_paquete = await db["data_paquetes"].insert_one(Paquete)
    created_paquete = await db["data_paquetes"].find_one({"_id":new_paquete.inserted_id})
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=created_paquete)