# ============================================================
# PaySentinelIQ — Integration Test Example
# Database repository tests
# ============================================================

import uuid
from datetime import datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.orm_models import EmployeeModel, TenantModel
from app.shared.repository import BaseRepository


@pytest.mark.asyncio
async def test_create_tenant(db_session: AsyncSession):
    """Test tenant creation via repository."""
    repo = BaseRepository(TenantModel, db_session)

    tenant = TenantModel(
        id=uuid.uuid4(),
        name="Test Corp",
        slug="test-corp",
        plan="professional",
    )
    saved = await repo.add(tenant)

    assert saved.id == tenant.id
    assert saved.name == "Test Corp"

    # Fetch it back
    fetched = await repo.get_by_id(tenant.id)
    assert fetched is not None
    assert fetched.name == "Test Corp"


@pytest.mark.asyncio
async def test_tenant_isolation(db_session: AsyncSession):
    """Test that get_all filters by tenant_id using EmployeeModel (has tenant_id FK)."""
    tenant_repo = BaseRepository(TenantModel, db_session)
    employee_repo = BaseRepository(EmployeeModel, db_session)

    tenant1_id = uuid.uuid4()
    tenant2_id = uuid.uuid4()

    await tenant_repo.add(TenantModel(id=tenant1_id, name="Tenant 1", slug="t1"))
    await tenant_repo.add(TenantModel(id=tenant2_id, name="Tenant 2", slug="t2"))

    now = datetime.now()
    emp1 = EmployeeModel(
        id=uuid.uuid4(),
        tenant_id=tenant1_id,
        full_name="Emp 1",
        email="e1@t1.com",
        department="Engineering",
        position="Developer",
        salary=100000.0,
        hire_date=now,
    )
    emp2 = EmployeeModel(
        id=uuid.uuid4(),
        tenant_id=tenant2_id,
        full_name="Emp 2",
        email="e2@t2.com",
        department="Engineering",
        position="Developer",
        salary=90000.0,
        hire_date=now,
    )
    await employee_repo.add(emp1)
    await employee_repo.add(emp2)

    # EmployeeModel has tenant_id, so filtering must return only
    # the employee belonging to the requested tenant
    results_t1 = await employee_repo.get_all(tenant1_id)
    assert len(results_t1) == 1
    assert results_t1[0].full_name == "Emp 1"

    results_t2 = await employee_repo.get_all(tenant2_id)
    assert len(results_t2) == 1
    assert results_t2[0].full_name == "Emp 2"


@pytest.mark.asyncio
async def test_count_records(db_session: AsyncSession):
    """Test repository count method — uses EmployeeModel for proper tenant_id filtering."""
    tenant_repo = BaseRepository(TenantModel, db_session)
    employee_repo = BaseRepository(EmployeeModel, db_session)

    tenant_id = uuid.uuid4()
    await tenant_repo.add(TenantModel(id=tenant_id, name="Test", slug="test"))

    now = datetime.now()
    for i in range(3):
        emp = EmployeeModel(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            full_name=f"Emp {i}",
            email=f"e{i}@test.com",
            department="Engineering",
            position="Developer",
            salary=80000.0,
            hire_date=now,
        )
        await employee_repo.add(emp)

    count = await employee_repo.count(tenant_id)
    assert count == 3
    assert isinstance(count, int)
