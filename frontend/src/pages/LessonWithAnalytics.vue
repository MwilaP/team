<template>
  <div v-if="lesson.data" class="">
    <header
      class="sticky top-0 z-10 flex items-center justify-between border-b bg-surface-white px-3 py-2.5 sm:px-5"
    >
      <Breadcrumbs class="h-7" :items="breadcrumbs" />
      <div class="flex items-center space-x-2">
        <Tooltip v-if="canGoZen()" :text="__('Zen Mode')">
          <Button @click="goFullScreen()">
            <template #icon>
              <Focus class="w-4 h-4 stroke-2" />
            </template>
          </Button>
        </Tooltip>
        <Button v-if="canSeeStats()" @click="showVideoStats()">
          <template #icon>
            <TrendingUp class="size-4 stroke-1.5" />
          </template>
        </Button>
        <CertificationLinks :courseName="courseName" />
        <Button v-if="lesson.data.prev" @click="switchLesson('prev')">
          <template #prefix>
            <ChevronLeft class="w-4 h-4 stroke-1" />
          </template>
          <span>
            {{ __('Previous') }}
          </span>
        </Button>

        <router-link
          v-if="allowEdit()"
          :to="{
            name: 'LessonForm',
            params: {
              courseName: courseName,
              chapterNumber: props.chapterNumber,
              lessonNumber: props.lessonNumber,
            },
          }"
        >
          <Button>
            {{ __('Edit') }}
          </Button>
        </router-link>

        <Button v-if="lesson.data.next" @click="switchLesson('next')">
          <template #suffix>
            <ChevronRight class="w-4 h-4 stroke-1" />
          </template>
          <span>
            {{ __('Next') }}
          </span>
        </Button>
      </div>
    </header>
    <div class="flex h-[calc(100vh-53px)]">
      <div
        v-if="!user && lesson.data.membership_required"
        class="flex h-full w-full flex-col items-center justify-center space-y-4 p-10"
      >
        <div class="flex items-center justify-center rounded-full bg-gray-100 p-4">
          <LockKeyholeIcon class="h-8 w-8 text-gray-600" />
        </div>
        <div class="text-center">
          <div class="text-xl font-medium">
            {{ __('Login Required') }}
          </div>
          <div class="mt-1 text-gray-600">
            {{ __('Please login to view this lesson') }}
          </div>
        </div>
        <div class="mt-4">
          <Button @click="login()">
            <template #prefix>
              <LogIn class="w-4 h-4 stroke-1" />
            </template>
            {{ __('Login') }}
          </Button>
        </div>
      </div>
      <div
        v-else
        ref="lessonContainer"
        class="bg-surface-white"
        :class="{
          'overflow-y-auto': zenModeEnabled,
        }"
      >
        <!-- Rest of the template content... -->
      </div>
    </div>
  </div>
</template>

<script setup>
import {
  Badge,
  Breadcrumbs,
  Button,
  call,
  createListResource,
  createResource,
  TabButtons,
  Tooltip,
  usePageMeta,
} from 'frappe-ui'
import {
  computed,
  watch,
  inject,
  ref,
  onMounted,
  onBeforeUnmount,
  nextTick,
} from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  ChevronLeft,
  ChevronRight,
  LockKeyholeIcon,
  LogIn,
  Focus,
  Info,
  MessageCircleQuestion,
  TrendingUp
} from 'lucide-vue-next'
import { sessionStore } from '../stores/session'
import { useSidebar } from '../stores/sidebar'
import learningAnalytics from '../lib/learning-analytics'
import EditorJS from '@editorjs/editorjs'
import LessonContent from '@/components/LessonContent.vue'
import CourseInstructors from '@/components/CourseInstructors.vue'
import ProgressBar from '@/components/ProgressBar.vue'
import Discussions from '@/components/Discussions.vue'
import CertificationLinks from '@/components/CertificationLinks.vue'
import VideoStatistics from '@/components/Modals/VideoStatistics.vue'
import CourseOutline from '@/components/CourseOutline.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import Notes from '@/components/Notes/Notes.vue'
import InlineLessonMenu from '@/components/Notes/InlineLessonMenu.vue'

const user = inject('$user')
const socket = inject('$socket')
const router = useRouter()
const route = useRoute()
const allowDiscussions = ref(false)
const editor = ref(null)
const instructorEditor = ref(null)
const lessonProgress = ref(0)
const lessonContainer = ref(null)
const zenModeEnabled = ref(false)
const showStatsDialog = ref(false)
const hasQuiz = ref(false)
const discussionsContainer = ref(null)
const timer = ref(0)
const { brand } = sessionStore()
const sidebarStore = useSidebar()

let timerInterval

const tabs = ref([
  {
    label: __('Notes'),
    value: 'Notes',
  },
])

const props = defineProps({
  courseName: {
    type: String,
    required: true,
  },
  chapterNumber: {
    type: String,
    required: true,
  },
  lessonNumber: {
    type: String,
    required: true,
  },
})

onMounted(() => {
  startTimer()
  sidebarStore.isSidebarCollapsed = true
  document.addEventListener('fullscreenchange', attachFullscreenEvent)
  socket.on('update_lesson_progress', (data) => {
    if (data.course === props.courseName) {
      lessonProgress.value = data.progress
    }
  })
  
  // Initialize learning analytics
  learningAnalytics.init()
  
  // Start tracking when lesson loads
  if (lesson.data) {
    startAnalyticsTracking()
  } else {
    // Wait for lesson data to load
    watch(() => lesson.data, (newValue) => {
      if (newValue) {
        startAnalyticsTracking()
      }
    })
  }
})

function startAnalyticsTracking() {
  if (lesson.data) {
    learningAnalytics.startSession(
      props.courseName,
      'lesson',
      lesson.data.name
    )
  }
}

const attachFullscreenEvent = () => {
  if (document.fullscreenElement) {
    zenModeEnabled.value = true
    allowDiscussions.value = false
  } else {
    zenModeEnabled.value = false
    if (!hasQuiz.value) {
      allowDiscussions.value = true
    }
  }
}

onBeforeUnmount(() => {
  document.removeEventListener('fullscreenchange', attachFullscreenEvent)
  sidebarStore.isSidebarCollapsed = false
  trackVideoWatchDuration()
  
  // End analytics tracking when navigating away
  learningAnalytics.endSession('navigate')
})

// Rest of the script content...

// Handle lesson switching with analytics
function switchLesson(direction) {
  // End current session
  learningAnalytics.endSession('navigate')
  
  // Original lesson switching logic
  if (direction === 'next' && lesson.data.next) {
    router.push({
      name: 'Lesson',
      params: {
        courseName: props.courseName,
        chapterNumber: lesson.data.next.chapter,
        lessonNumber: lesson.data.next.lesson,
      },
    })
  } else if (direction === 'prev' && lesson.data.prev) {
    router.push({
      name: 'Lesson',
      params: {
        courseName: props.courseName,
        chapterNumber: lesson.data.prev.chapter,
        lessonNumber: lesson.data.prev.lesson,
      },
    })
  }
}

// Rest of the script content...
</script>

<style>
/* Original styles... */
</style>
