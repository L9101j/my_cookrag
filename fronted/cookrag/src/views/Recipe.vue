<template>
  <div class="recipe-container">
    <div class="header">
      <h2>浏览食谱</h2>
    </div>
    <div class="filter-bar">
     <el-radio-group v-model="categoryOptions">
        <el-radio-button label="荤菜">荤菜</el-radio-button>
        <el-radio-button label="素菜">素菜</el-radio-button>
        <el-radio-button label="汤品">汤品</el-radio-button>
        <el-radio-button label="甜品">甜品</el-radio-button>
        <el-radio-button label="早餐">早餐</el-radio-button>
        <el-radio-button label="主食">主食</el-radio-button>
        <el-radio-button label="水产">水产</el-radio-button>
        <el-radio-button label="调料">调料</el-radio-button>
        <el-radio-button label="饮品">饮品</el-radio-button>
      </el-radio-group>
    
      <el-select v-model="difficultyOptions" placeholder="选择难度" style="width: 200px; margin-left: 20px;">
        <el-option
          v-for="difficulty in ['非常简单', '简单', '中等', '困难', '非常困难']"
          :key="difficulty"
          :label="difficulty"
          :value="difficulty"
        />
      </el-select>

      <el-button type="primary" @click="handleSearch" style="margin-left: 20px;">搜索</el-button>
    </div>

    <el-row :gutter="20" v-loading="loading">
      <el-col :xs="24" :sm="12" :md="8" :lg="6" v-for="recipe in recipes" :key="recipe.id">
        <el-card :body-style="{ padding: '0px' }" class="recipe-card" >
          <div class="image-placeholder">
            <el-icon :size="50" color="#909399"><Food /></el-icon>
          </div>
          <div style="padding: 14px">
            <span>{{ recipe.name }}</span>
            <div class="bottom">
              <el-tag size="small">{{ recipe.category }}</el-tag>
              <el-button text class="button" @click="openDetail(recipe)">查看详情</el-button>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="detailVisible" :title="currentRecipe.name" width="80%">
      <div class="recipe-content">
     {{ currentRecipe.content }}
      </div>
      <el-button type="primary" @click="detailVisible = false">关闭</el-button>
    </el-dialog>


    <el-pagination
      v-model:current-page="currentPage"
      size="large"
      :page-size="pageSize"
      background layout="prev, pager, next"
      :total="total"
      style="margin-top: 20px; text-align: right;"
      @current-change="handlePageChange"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { Food, Loading } from '@element-plus/icons-vue'
import apiClient from '@/service/api'


type Difficulty = | '非常简单'
  | '简单'
  | '中等'
  | '困难'
  | '非常困难'
  | '未知'

interface RecipeListQuery {
  category?: string
  difficulty?: Difficulty
  page?: number
  page_size?: number
}
interface RecipePreview {
  id: number
  name: string
  category: string
  difficulty?: Difficulty
  preview?: string
}
interface RecipeDetail {
  id: number
  name: string
  content: string
  category: string
  difficulty: Difficulty
}


const categoryOptions = ref<string>('')
const difficultyOptions = ref<Difficulty | ''>('') 
const pageSize = ref(12)        
const currentPage = ref(1) 
const total = ref(0) 
const recipes = ref<RecipePreview[]>([])  
const detailVisible = ref(false)
const currentRecipe = ref<RecipeDetail>({ id: 0, name: '', content: '', category: '', difficulty: '未知' })
const loading = ref(true)

const getRecipeListQuery = (): RecipeListQuery => {
  return {
    category: categoryOptions.value || undefined,
    difficulty: (difficultyOptions.value || undefined) as Difficulty | undefined,
    page: currentPage.value,
    page_size: pageSize.value,
  }
}

const getRecipes = async() => {
  const query = getRecipeListQuery()
  try {
    const response = await apiClient.get('/api/surf/recipes', { params: query })
    console.log('获取食谱列表:', response)
    const recipelist = response.data.data.recipes 
    recipes.value = recipelist
    total.value = response.data.data.total
    currentPage.value = response.data.data.page
    pageSize.value = response.data.data.page_size
    loading.value = false
  } catch (error) {
    console.error('获取食谱列表失败:', error)
  }
}

const getRecipeDetails = async(recipeId: number) => {
  try {
    const response = await apiClient.get(`/api/surf/${recipeId}/detail`)
    console.log('获取食谱详情:', response)
    return response.data.data
  } catch (error) {
    console.error('获取食谱详情失败:', error)
    return null
  }
}

const openDetail = async(recipe: RecipePreview) => {
  const detail = await getRecipeDetails(recipe.id)
  if (detail) {
    currentRecipe.value = detail
    detailVisible.value = true
  }
}

// 搜索时重置到第 1 页再拉取
const handleSearch = () => {
  currentPage.value = 1
  getRecipes()
}

// 页码变更时触发
const handlePageChange = (page: number) => {
  currentPage.value = page
  getRecipes()
}

// 页面加载时拉一次
onMounted(() => {
  getRecipes()
})


</script>

<style scoped>
.recipe-container {
  padding: 20px;
}
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.recipe-card {
  margin-bottom: 20px;
  cursor: pointer;
  transition: transform 0.3s;
}
.recipe-card:hover {
  transform: translateY(-5px);
}
.image-placeholder {
  width: 100%;
  height: 150px;
  background-color: #f0f2f5;
  display: flex;
  align-items: center;
  justify-content: center;
}
.bottom {
  margin-top: 13px;
  line-height: 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.button {
  padding: 0;
  min-height: auto;
}
.el-pagination {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}
.filter-bar {
  display: flex;
  justify-content: start;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap; /* 小屏时自动换行 */
  gap: 12px;
}
.category-group {
  flex: 1;
  min-width: 260px;
}

.search-button {
  white-space: nowrap;
}
.recipe-content {
  white-space: pre-wrap;   /* 保留换行和多空格，并在需要时自动换行 */
  font-size: 14px;         /* 这里控制字体大小 */
  line-height: 1.6;        /* 行高可按需求调整 */
}


</style>