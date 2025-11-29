from fastapi import APIRouter, Depends, HTTPException
from ..schema import (
    ApiResponse,
    RecipeListQuery,
    RecipePreview,
    RecipeListResponse,
    RecipeDetail
)
from ..dependency import get_db_manager, create_api_response, create_error_response


router = APIRouter(prefix="/surf", tags=["浏览API"])

@router.get("/recipes", response_model=ApiResponse, description='获取菜谱列表')
async def get_recipe_list(query: RecipeListQuery = Depends(), db_manager=Depends(get_db_manager)):
    """
    获取菜谱列表，支持按分类和难度过滤
    """
    try:
        # 提取查询参数  
        category = query.category
        difficulty = query.difficulty
        page = query.page
        page_size = query.page_size
        # 根据参数获取对应的食谱列表（同步方法，无需 await）
        total, recipes = db_manager.select_recipes(page, page_size, category, difficulty)
        recipes_previews_list = [
            RecipePreview(
                id=recipe.id,
                name=recipe.name,
                category=recipe.category,
                difficulty=recipe.difficulty,
                preview=recipe.content[:100] + "..." if len(recipe.content) > 100 else recipe.content
            ) for recipe in recipes
        ]
        response_data = RecipeListResponse(
            total=total,
            page=page,
            page_size=page_size,
            recipes=recipes_previews_list
        )
        return create_api_response(data=response_data)

    except Exception as e:
        return create_error_response(message=f"获取菜谱列表失败: {e}", code=500, error_type="DatabaseError", details=str(e))

@router.get("/{recipe_id}/detail",response_model=ApiResponse,description='获取菜谱详情')
async def get_detailed_recipe(recipe_id: int, db_manager=Depends(get_db_manager)):
    """
    获取指定菜谱的详细信息
    """
    try:
        # 从数据库获取菜谱详情（同步方法，无需 await）
        recipe = db_manager.select_recipe_by_id(recipe_id)
        if not recipe:
            return create_error_response(message="菜谱不存在", code=404, error_type="NotFoundError")
        # 构建详细信息响应
        recipe_detail = RecipeDetail(
            id=recipe.id,
            name=recipe.name,
            category=recipe.category,
            difficulty=recipe.difficulty,
            content=recipe.content
        )
        return create_api_response(data=recipe_detail)
    except Exception as e:
        return create_error_response(message=f"获取菜谱详情失败: {e}", code=500, error_type="DatabaseError", details=str(e))


