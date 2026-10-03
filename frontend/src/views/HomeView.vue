<template>
  <div id="app-shell" :class="{ 'legacy-mode': legacyLayout }">
    <!-- 顶部操作栏：设置存取 + 生成操作 -->
    <header class="app-header" data-testid="app-header">
      <div class="header-bar">
        <div class="app-title">{{ $t('message.appTitle') }}</div>
        <div class="header-actions">
          <button class="action-btn secondary" data-testid="load-settings-btn" @click="loadPreset">{{ $t('message.loadSettings') }}</button>
          <button class="action-btn secondary" data-testid="save-settings-btn" @click="savePreset">{{ $t('message.saveSettings') }}</button>
          <button class="action-btn secondary" data-testid="reset-settings-btn" @click="resetSettings">{{ $t('message.resetSettings') }}</button>
          <span class="header-divider" aria-hidden="true"></span>
          <button class="action-btn primary" data-testid="preview-btn" @click="generateHandwriting(preview = true)"
            :disabled="shouldDisableButtons">
            {{ buttonText || $t('message.preview') }}
          </button>
          <button v-if="isDevEnv" class="action-btn secondary" data-testid="full-preview-toggle-btn" @click="toggleFullPreview"
            :disabled="shouldDisableButtons">
            本地全量预览：{{ enableFullPreview ? '开' : '关' }}
          </button>
          <button class="action-btn primary" data-testid="generate-image-btn" @click="generateHandwriting(preview = false)"
            :disabled="shouldDisableButtons">
            {{ buttonText || $t('message.generateFullHandwritingImage') }}
          </button>
          <button class="action-btn primary" data-testid="generate-pdf-btn" @click="generateHandwriting(preview = false, pdf_save = true)"
            :disabled="shouldDisableButtons">
            {{ buttonText || $t('message.generatePdf') }}
          </button>
          <router-link to="/Feedback" class="action-btn info">{{ $t('message.feedback') }}</router-link>
          <button class="action-btn secondary" data-testid="layout-toggle-btn" @click="toggleLayout">
            {{ legacyLayout ? $t('message.newLayout') : $t('message.legacyLayout') }}
          </button>
        </div>
      </div>

      <!-- 错误消息以及提示信息 -->
      <div id="message">
        <div v-if="message" class="alert alert-info" role="alert" data-testid="message-info">
          {{ message }}
        </div>
        <div v-if="uploadMessage" class="alert alert-info" role="alert" data-testid="message-upload">
          {{ uploadMessage }}
        </div>
      </div>

      <!-- 供 e2e 核对实际交付的 PDF 体积，平时不占位（见 e2e/tests/home-generate.spec.js） -->
      <span v-if="lastPdfDownloadBytes > 0" data-testid="pdf-download-bytes" style="display: none;">{{
        lastPdfDownloadBytes }}</span>
    </header>

    <!-- 三栏工作区：左=参数，中=正文，右=预览 -->
    <div v-if="!legacyLayout" class="workspace" data-testid="workspace" ref="workspace"
      :style="workspaceStyle">
      <!-- 左栏：参数设置 -->
      <aside class="panel panel-settings" data-testid="panel-settings" ref="panelSettings">
        <h2 class="panel-title">{{ $t('message.settingsPanel') }}</h2>

        <label class="field-label" for="fontSelect">{{ $t('message.fontFile') }}:</label>
        <div class="font-selection">
          <button class="action-btn secondary small" data-testid="font-file-btn" @click="triggerFontFileInput">{{ $t('message.chooseFile') }}</button>
          <input type="file" ref="fontFileInput" data-testid="font-file-input" @change="onFontChange" style="display: none;" />
          <select id="fontSelect" v-model="selectedOption" class="styled-select font-select" data-testid="font-select">
            <option v-for="option in options" :value="option.value" :key="option.value">
              {{ option.text }}
            </option>
          </select>
        </div>

        <label class="field-label">{{ $t('message.backgroundImageFile') }}:</label>
        <div class="image-container">
          <div class="button-container">
            <button class="action-btn secondary small" data-testid="background-image-btn" @click="triggerImageFileInput"
              :class="{ 'button-disabled': isDimensionSpecified }"
              :title="isDimensionSpecified ? $t('message.widthAndHeightSpecified') : ''">
              {{ $t('message.chooseFile') }}
              <div>
                <div v-if="selectedImageFileName" class="clear-button" @click.stop="clearImage">
                  <div class="clear-button-line"></div>
                  <div class="clear-button-line"></div>
                </div>
              </div>
            </button>
            <span class="border p-2 fs-6 text-primary nowrap" v-if="selectedImageFileName">{{ selectedImageFileName }}</span>
            <input type="file" ref="imageFileInput" data-testid="background-image-input"
              @change="onBackgroundImageChange" style="display: none;" />
            <div v-if="isLoading" class="loader">{{ $t('message.loading') }}...</div>
          </div>
        </div>

        <div class="label-container">
          <label for="widthInput">{{ $t('message.width') }}:</label>
          <input id="widthInput" type="number" v-model="width" data-testid="width-input" :disabled="isBackgroundImageSpecified"
            :title="isBackgroundImageSpecified ? $t('message.backgroundImageSpecified') : ''" />
        </div>

        <div class="label-container">
          <label for="heightInput">{{ $t('message.height') }}:</label>
          <input id="heightInput" type="number" v-model="height" data-testid="height-input" :disabled="isBackgroundImageSpecified"
            :title="isBackgroundImageSpecified ? $t('message.backgroundImageSpecified') : ''" />
          <button type="button" class="close" aria-label="Close" @click="clearDimensions">
            <span aria-hidden="true">&times;</span>
          </button>
        </div>

        <div class="check-container">
          <input class="optionUnderline" type="checkbox" id="optionUnderline" name="option2" value="value2" v-model="isUnderlined">
          <label for="optionUnderline">{{ $t('message.underline') }}</label>
        </div>

        <div class="check-container">
          <input class="optionEnglishSpacing" type="checkbox" id="optionEnglishSpacing" name="optionEnglishSpacing"
            value="englishSpacing" v-model="enableEnglishSpacing">
          <label for="optionEnglishSpacing">{{ $t('message.enableEnglishSpacing') }}</label>
        </div>

        <div class="label-container">
          <label for="fontSizeInput">{{ $t('message.fontSize') }}:</label>
          <input id="fontSizeInput" type="number" v-model="fontSize" data-testid="font-size-input" placeholder="recommend > 100" />
        </div>

        <div class="label-container">
          <label for="lineSpacingInput">{{ $t('message.lineSpacing') }}:</label>
          <input id="lineSpacingInput" type="number" v-model="lineSpacing" data-testid="line-spacing-input" />
        </div>

        <div class="label-container">
          <label for="marginTopInput">{{ $t('message.topMargin') }}:</label>
          <input id="marginTopInput" type="number" v-model="marginTop" data-testid="margin-top-input" />
        </div>

        <div class="label-container">
          <label for="marginBottomInput">{{ $t('message.bottomMargin') }}:</label>
          <input id="marginBottomInput" type="number" v-model="marginBottom" data-testid="margin-bottom-input" />
        </div>

        <div class="label-container">
          <label for="marginLeftInput">{{ $t('message.leftMargin') }}:</label>
          <input id="marginLeftInput" type="number" v-model="marginLeft" data-testid="margin-left-input" />
        </div>

        <div class="label-container">
          <label for="marginRightInput">{{ $t('message.rightMargin') }}:</label>
          <input id="marginRightInput" type="number" v-model="marginRight" data-testid="margin-right-input" />
        </div>

        <!-- 展开/折叠高级参数 -->
        <button class="btn btn-primary advanced-toggle" type="button" data-testid="toggle-advanced-btn" @click="toggleCollapse">
          {{ $t('message.expand') }}
        </button>

        <div v-if="isExpanded" id="collapseContent">
          <div class="card card-body">
            <div class="label-container">
              <label>{{ $t('message.lineSpacingSigma') }}:
                <input type="number" v-model="lineSpacingSigma" />
              </label>
            </div>

            <div class="label-container">
              <label>{{ $t('message.fontSizeSigma') }}:
                <input type="number" v-model="fontSizeSigma" />
              </label>
            </div>

            <div class="label-container">
              <label>{{ $t('message.wordSpacingSigma') }}:
                <input type="number" v-model="wordSpacingSigma" />
              </label>
            </div>

            <div class="label-container">
              <label>{{ $t('message.perturbXSigma') }}:
                <input type="number" v-model="perturbXSigma" />
              </label>
            </div>

            <div class="label-container">
              <label>{{ $t('message.perturbYSigma') }}:
                <input type="number" v-model="perturbYSigma" />
              </label>
            </div>

            <div class="label-container">
              <label>{{ $t('message.perturbThetaSigma') }}:
                <input type="number" v-model="perturbThetaSigma" />
              </label>
            </div>

            <div class="label-container">
              <label>{{ $t('message.wordSpacing') }}:
                <input type="number" v-model="wordSpacing" />
              </label>
            </div>

            <div class="label-container">
              <label>{{ $t('message.strikethrough_length_sigma') }}:
                <input type="text" v-model="strikethrough_length_sigma" />
              </label>
            </div>

            <div class='label-container'>
              <label>{{ $t('message.strikethrough_angle_sigma') }}:
                <input type="number" v-model="strikethrough_angle_sigma" />
              </label>
            </div>

            <div class='label-container'>
              <label>{{ $t('message.strikethrough_width_sigma') }}:
                <input type="number" v-model="strikethrough_width_sigma" />
              </label>
            </div>

            <div class='label-container'>
              <label>{{ $t('message.strikethrough_probability') }}:
                <input type="number" v-model="strikethrough_probability" />
              </label>
            </div>

            <div class='label-container'>
              <label>{{ $t('message.strikethrough_width') }}:
                <input type="number" v-model="strikethrough_width" />
              </label>
            </div>

            <div class='label-container'>
              <label>{{ $t('message.ink_depth_sigma') }}:
                <input type="number" v-model="ink_depth_sigma" />
              </label>
            </div>
          </div>
        </div>

        <div class="preset-row">
          <label for="builtinPreset">{{ $t('message.presetLabel') }}:</label>
          <select id="builtinPreset" :value="selectedPreset" @change="applyPreset" class="styled-select"
            data-testid="builtin-preset-select" :disabled="!presetOptionsReady">
            <option value="">{{ $t('message.presetNone') }}</option>
            <option value="smallUnderlined">{{ $t('message.presetSmallUnderlined') }}</option>
          </select>
        </div>
      </aside>

      <!-- 分隔条：左右拖动调整左栏宽度，双击恢复默认 -->
      <div class="resizer" data-testid="resizer-settings" role="separator" aria-orientation="vertical"
        :class="{ active: resizeState && resizeState.side === 'left' }"
        :aria-label="$t('message.resizeColumnLeft')" :title="$t('message.resizeColumnHint')" tabindex="0"
        @pointerdown="startResize('left', $event)" @pointermove="onResizeMove" @pointerup="endResize"
        @pointercancel="endResize" @dblclick="resetColumnWidth('left')"
        @keydown="onResizerKeydown('left', $event)"></div>

      <!-- 中栏：正文 -->
      <main class="panel panel-text" data-testid="panel-text" ref="panelText">
        <h2 class="panel-title">{{ $t('message.text') }}</h2>

        <TextInput class="text-input-fill" ref="textInputComp" @childEvent="(eventData) => { this.text = eventData }"
          @manual-input="clearLetterFormatBackup"></TextInput>

        <div class="letter-format-actions">
          <button type="button" class="letter-format-button" data-testid="letter-format-btn" @click="openLetterFormatter">
            <span class="letter-format-mark" aria-hidden="true">信</span>
            {{ $t('message.formatChineseLetter') }}
          </button>
          <button v-if="letterFormatBackup !== null" type="button" class="letter-format-undo"
            data-testid="letter-undo-btn" @click="undoLetterFormatting">
            {{ $t('message.letterUndo') }}
          </button>
        </div>

        <!-- 生成状态提示与页数提示（新旧两版共用同一个组件） -->
        <GenerationStatus :generating="isGenerating" :cooldown-seconds="remainingCooldown"
          :page-count="estimatedPages" />
      </main>

      <!-- 分隔条：左右拖动调整右栏宽度，双击恢复默认 -->
      <div class="resizer" data-testid="resizer-preview" role="separator" aria-orientation="vertical"
        :class="{ active: resizeState && resizeState.side === 'right' }"
        :aria-label="$t('message.resizeColumnRight')" :title="$t('message.resizeColumnHint')" tabindex="0"
        @pointerdown="startResize('right', $event)" @pointermove="onResizeMove" @pointerup="endResize"
        @pointercancel="endResize" @dblclick="resetColumnWidth('right')"
        @keydown="onResizerKeydown('right', $event)"></div>

      <!-- 右栏：预览 -->
      <section class="panel panel-preview" data-testid="panel-preview" ref="panelPreview">
        <h2 class="panel-title">{{ $t('message.preview') }}</h2>

        <div class="preview-container text-center">
          <!-- 导航按钮 -->
          <div v-if="previewImages && previewImages.length > 1" class="preview-nav">
            <button @click="prevPage" data-testid="preview-prev-btn" class="btn btn-outline-primary btn-sm"
              :disabled="currentPreviewIndex === 0">
              &larr; {{ $t('message.prevPage') }}
            </button>
            <span class="preview-page-indicator" data-testid="preview-page-indicator">
              {{ $t('message.pageIndicator', { current: currentPreviewIndex + 1, total: previewImages.length }) }}
            </span>
            <button @click="nextPage" data-testid="preview-next-btn" class="btn btn-outline-primary btn-sm"
              :disabled="currentPreviewIndex === previewImages.length - 1">
              {{ $t('message.nextPage') }} &rarr;
            </button>
          </div>

          <!-- 图片显示 -->
          <div v-if="previewImages && previewImages.length > 0">
            <img :src="previewImages[currentPreviewIndex]" data-testid="preview-image" class="preview-image"
              :alt="$t('message.previewImage') + ' ' + (currentPreviewIndex + 1)" />
          </div>
          <img v-else :src="previewImage" data-testid="preview-image" :alt="$t('message.previewImage')"
            class="preview-image" />
        </div>
      </section>
    </div>

    <!-- 旧版布局：改造前的表单 + 右侧预览，可用顶栏「旧版界面」按钮切回 -->
    <div v-else class="legacy-root" data-testid="legacy-layout">
      <div id="form">
        <div class="container_file row">

          <div class="col justify-content-between">
            <TextInput ref="textInputComp" @childEvent="(eventData) => { this.text = eventData }"
              @manual-input="clearLetterFormatBackup"></TextInput>
            <div class="letter-format-actions">
              <button type="button" class="letter-format-button" data-testid="letter-format-btn"
                @click="openLetterFormatter">
                <span class="letter-format-mark" aria-hidden="true">信</span>
                {{ $t('message.formatChineseLetter') }}
              </button>
              <button v-if="letterFormatBackup !== null" type="button" class="letter-format-undo"
                data-testid="letter-undo-btn" @click="undoLetterFormatting">
                {{ $t('message.letterUndo') }}
              </button>
            </div>
          </div>

          <div class="col">
            <label>{{ $t('message.fontFile') }}:</label>
            <div class="d-flex flex-row justify-content-between">
              <div class="font-selection">
                <button data-testid="font-file-btn" @click="triggerFontFileInput">{{ $t('message.chooseFile') }}</button>
                <input type="file" ref="fontFileInput" data-testid="font-file-input" @change="onFontChange"
                  style="display: none;" />
              </div>
              <select v-model="selectedOption" class="styled-select" data-testid="font-select" style="width: 60%;">
                <option v-for="option in options" :value="option.value" :key="option.value">
                  {{ option.text }}
                </option>
              </select>
            </div>

            <div class="image-container">
              <label>{{ $t('message.backgroundImageFile') }}:</label>
              <div class="button-container">
                <button data-testid="background-image-btn" @click="triggerImageFileInput"
                  :class="{ 'button-disabled': isDimensionSpecified }"
                  :title="isDimensionSpecified ? $t('message.widthAndHeightSpecified') : ''">
                  {{ $t('message.chooseFile') }}
                  <div>
                    <div v-if="selectedImageFileName" class="clear-button" @click.stop="clearImage">
                      <div class="clear-button-line"></div>
                      <div class="clear-button-line"></div>
                    </div>
                  </div>
                </button>
                <span class="border p-2 fs-6 text-primary nowrap" v-if="selectedImageFileName">{{ selectedImageFileName }}</span>
                <input type="file" ref="imageFileInput" data-testid="background-image-input"
                  @change="onBackgroundImageChange" style="display: none;" />
                <div v-if="isLoading" class="loader">{{ $t('message.loading') }}...</div>
              </div>
            </div>
          </div>
        </div>

        <div class="label-container">
          <label>{{ $t('message.width') }}:
            <input type="number" v-model="width" data-testid="width-input" :disabled="isBackgroundImageSpecified"
              :title="isBackgroundImageSpecified ? $t('message.backgroundImageSpecified') : ''" />
          </label>
        </div>

        <div class="label-container">
          <label>{{ $t('message.height') }}:
            <input type="number" v-model="height" data-testid="height-input" :disabled="isBackgroundImageSpecified"
              :title="isBackgroundImageSpecified ? $t('message.backgroundImageSpecified') : ''" />
          </label>
          <button type="button" class="close" aria-label="Close" @click="clearDimensions">
            <span aria-hidden="true">&times;</span>
          </button>
        </div>

        <input class="optionUnderline" type="checkbox" id="optionUnderline" name="option2" value="value2"
          v-model="isUnderlined">
        <label for="optionUnderline" style="margin-right: 0px;">{{ $t('message.underline') }}</label>

        <input class="optionEnglishSpacing" type="checkbox" id="optionEnglishSpacing" name="optionEnglishSpacing"
          value="englishSpacing" v-model="enableEnglishSpacing">
        <label for="optionEnglishSpacing" style="margin-right: 0px;">{{ $t('message.enableEnglishSpacing') }}</label>

        <div class="label-container">
          <label>{{ $t('message.fontSize') }}:
            <input type="number" v-model="fontSize" data-testid="font-size-input" placeholder="recommend > 100" />
          </label>
        </div>

        <div class="label-container">
          <label>{{ $t('message.lineSpacing') }}:
            <input type="number" v-model="lineSpacing" data-testid="line-spacing-input" />
          </label>
        </div>

        <div class="label-container">
          <label>{{ $t('message.topMargin') }}:
            <input type="number" v-model="marginTop" data-testid="margin-top-input" />
          </label>
        </div>

        <div class="label-container">
          <label>{{ $t('message.bottomMargin') }}:
            <input type="number" v-model="marginBottom" data-testid="margin-bottom-input" />
          </label>
        </div>

        <div class="label-container">
          <label>{{ $t('message.leftMargin') }}:
            <input type="number" v-model="marginLeft" data-testid="margin-left-input" />
          </label>
        </div>

        <div class="label-container">
          <label>{{ $t('message.rightMargin') }}:
            <input type="number" v-model="marginRight" data-testid="margin-right-input" />
          </label>
        </div>

        <!-- 展开/折叠高级参数 -->
        <button class="btn btn-primary" type="button" data-testid="toggle-advanced-btn" @click="toggleCollapse"
          style="width: 100px; font-size:0.9rem">
          {{ $t('message.expand') }}
        </button>

        <div v-if="isExpanded" id="collapseContent">
          <div class="card card-body">
            <div class="label-container">
              <label>{{ $t('message.lineSpacingSigma') }}:
                <input type="number" v-model="lineSpacingSigma" />
              </label>
            </div>

            <div class="label-container">
              <label>{{ $t('message.fontSizeSigma') }}:
                <input type="number" v-model="fontSizeSigma" />
              </label>
            </div>

            <div class="label-container">
              <label>{{ $t('message.wordSpacingSigma') }}:
                <input type="number" v-model="wordSpacingSigma" />
              </label>
            </div>

            <div class="label-container">
              <label>{{ $t('message.perturbXSigma') }}:
                <input type="number" v-model="perturbXSigma" />
              </label>
            </div>

            <div class="label-container">
              <label>{{ $t('message.perturbYSigma') }}:
                <input type="number" v-model="perturbYSigma" />
              </label>
            </div>

            <div class="label-container">
              <label>{{ $t('message.perturbThetaSigma') }}:
                <input type="number" v-model="perturbThetaSigma" />
              </label>
            </div>

            <div class="label-container">
              <label>{{ $t('message.wordSpacing') }}:
                <input type="number" v-model="wordSpacing" />
              </label>
            </div>

            <div class="label-container">
              <label>{{ $t('message.strikethrough_length_sigma') }}:
                <input type="text" v-model="strikethrough_length_sigma" />
              </label>
            </div>

            <div class='label-container'>
              <label>{{ $t('message.strikethrough_angle_sigma') }}:
                <input type="number" v-model="strikethrough_angle_sigma" />
              </label>
            </div>

            <div class='label-container'>
              <label>{{ $t('message.strikethrough_width_sigma') }}:
                <input type="number" v-model="strikethrough_width_sigma" />
              </label>
            </div>

            <div class='label-container'>
              <label>{{ $t('message.strikethrough_probability') }}:
                <input type="number" v-model="strikethrough_probability" />
              </label>
            </div>

            <div class='label-container'>
              <label>{{ $t('message.strikethrough_width') }}:
                <input type="number" v-model="strikethrough_width" />
              </label>
            </div>

            <div class='label-container'>
              <label>{{ $t('message.ink_depth_sigma') }}:
                <input type="number" v-model="ink_depth_sigma" />
              </label>
            </div>
          </div>
        </div>

        <div class="preset-row">
          <label for="builtinPreset">{{ $t('message.presetLabel') }}:</label>
          <select id="builtinPreset" :value="selectedPreset" @change="applyPreset" class="styled-select"
            data-testid="builtin-preset-select" :disabled="!presetOptionsReady">
            <option value="">{{ $t('message.presetNone') }}</option>
            <option value="smallUnderlined">{{ $t('message.presetSmallUnderlined') }}</option>
          </select>
        </div>
      </div>

      <!-- 生成状态与页数提示：和改造前一样，旧版里也要显示 -->
      <GenerationStatus :generating="isGenerating" :cooldown-seconds="remainingCooldown"
        :page-count="estimatedPages" />

      <div class="preview" data-testid="preview-area">
        <h2 v-if="!previewImages || previewImages.length === 0">{{ $t('message.preview') }}:</h2>

        <div class="preview-container text-center">
          <div v-if="previewImages && previewImages.length > 1"
            class="mb-3 d-flex justify-content-center align-items-center gap-3">
            <button @click="prevPage" data-testid="preview-prev-btn" class="btn btn-outline-primary btn-sm"
              :disabled="currentPreviewIndex === 0">
              &larr; {{ $t('message.prevPage') }}
            </button>
            <span class="mx-3 font-weight-bold" data-testid="preview-page-indicator">
              {{ $t('message.pageIndicator', { current: currentPreviewIndex + 1, total: previewImages.length }) }}
            </span>
            <button @click="nextPage" data-testid="preview-next-btn" class="btn btn-outline-primary btn-sm"
              :disabled="currentPreviewIndex === previewImages.length - 1">
              {{ $t('message.nextPage') }} &rarr;
            </button>
          </div>

          <div v-if="previewImages && previewImages.length > 0">
            <img :src="previewImages[currentPreviewIndex]" data-testid="preview-image"
              :alt="$t('message.previewImage') + ' ' + (currentPreviewIndex + 1)"
              style="width: 600px; max-width: 100%; border: 1px solid #ddd; padding: 5px; border-radius: 4px;" />
          </div>
          <img v-else :src="previewImage" data-testid="preview-image" :alt="$t('message.previewImage')"
            style="width: 600px; max-width: 100%;" />
        </div>
      </div>
    </div>

    <ChineseLetterFormatter v-if="showLetterFormatter" :source-text="text" @close="showLetterFormatter = false"
      @apply="applyLetterFormatting" />

    <footer class="footer mt-auto py-3 bg-white" data-testid="site-footer">
      <div class="container text-center">
        <!-- <a href="mailto:14790897abc@gmail.com" class="text-info">14790897abc@gmail.com</a> -->
        <span class="text-black">{{ $t('message.projectAddress') }}:</span>
        <a href="https://github.com/14790897/handwriting-web" class="text-info">GitHub</a>
        <span v-if="appVersion" data-testid="app-version" class="version-tag">v{{ appVersion }}</span>
      </div>
      <!-- 本网站是免费网站如果你是付费访问的请退款 -->
      <div class="freeprompt">{{ $t('message.freeprompt') }}</div>
    </footer>
  </div>
</template>

<script>
import { mapState } from 'vuex';
import TextInput from './TextInput.vue';
import ChineseLetterFormatter from '../components/ChineseLetterFormatter.vue';
import GenerationStatus from '../components/GenerationStatus.vue';
import Swal from 'sweetalert2';

const BUILTIN_PRESETS = {
  smallUnderlined: {
    fontName: '云烟体.ttf',
    values: {
      fontSize: 70,
      lineSpacing: 100,
      width: 2481,
      height: 3507,
      marginTop: 150,
      marginBottom: 150,
      marginLeft: 150,
      marginRight: 150,
      lineSpacingSigma: 1,
      fontSizeSigma: 1,
      wordSpacingSigma: 2,
      perturbXSigma: 1,
      perturbYSigma: 1,
      perturbThetaSigma: 0.05,
      wordSpacing: 2,
      strikethrough_length_sigma: 2,
      strikethrough_angle_sigma: 2,
      strikethrough_width_sigma: 2,
      strikethrough_probability: 0,
      strikethrough_width: 8,
      ink_depth_sigma: 30,
      isUnderlined: true,
      enableEnglishSpacing: false,
    },
  },
};



// 三栏拖动：左右两栏各自的最小宽度、中栏的最小宽度（px），
// 以及 CSS 里那条间隔轨道的宽度（分隔条的拖动热区就画在它上面）
const MIN_COLUMN_WIDTH = 200;
const MIN_MIDDLE_WIDTH = 300;
const GUTTER_WIDTH = 16;
// 分隔条拿到键盘焦点后，左右方向键每次调整的像素
const KEYBOARD_RESIZE_STEP = 20;

const clamp = (value, min, max) => Math.min(Math.max(value, min), max);

export default {
  // props: {
  //   login_delete_message: {
  //     type: Boolean,
  //     default: false
  //   }
  // },
  components: {
    TextInput,
    ChineseLetterFormatter,
    GenerationStatus,

  },

  data() {
    return {
      text: "",
      // 页面底部展示的版本号，来自 /api/version；取不到就不显示
      appVersion: "",
      fontFile: null,
      backgroundImage: null,
      fontSize: 124,
      lineSpacing: 200,
      fill: "(0, 0, 0, 255)",
      width: 2481,
      height: 3507,
      marginTop: 50,
      marginBottom: 50,
      marginLeft: 50,
      marginRight: 50,
      previewImage: "/default1.webp", // 添加一个新的数据属性来保存预览图片的 URL
      previewImages: [], // 用于存储多页预览图片的数组
      currentPreviewIndex: 0, // 当前预览的图片索引
      preview: false,
      lineSpacingSigma: 0,
      fontSizeSigma: 2,
      wordSpacingSigma: 2,
      perturbXSigma: 3,
      perturbYSigma: 3,
      perturbThetaSigma: 0.05,
      wordSpacing: 1,
      endChars: '',
      errorMessage: '',  // 错误消息
      message: '',  // 提示消息
      uploadMessage: '',  // 上传提示消息
      lastPdfDownloadBytes: 0,  // 最近一次 PDF 下载的字节数，供 e2e 核对
      selectedFontFileName: '',
      selectedImageFileName: '',
      //字体下拉选框
      selectedOption: '1',  // 当前选中的选项
      selectedPreset: '',
      builtinPresets: BUILTIN_PRESETS,
      options: '',  // 下拉选项
      isLoading: false, //7.6
      strikethrough_length_sigma: 2,
      strikethrough_angle_sigma: 2,
      strikethrough_width_sigma: 2,
      strikethrough_probability: 0.005,
      strikethrough_width: 8,
      ink_depth_sigma: 30,
      isUnderlined: true,
      enableEnglishSpacing: false,
      isExpanded: false,
      // 生成状态控制
      isGenerating: false,
      lastGenerateTime: 0,
      generateCooldown: 3000, // 3秒冷却时间
      cooldownTimer: null,
      remainingCooldown: 0,
      isInCooldownPeriod: false,
      // 队列满倒计时
      queueFullCountdown: 0,        // 当前剩余秒数，>0 时展示提示
      queueFullTotal: 0,            // 初始等待秒数，用于计算进度条
      queueFullTimer: null,         // setInterval 句柄
      enableFullPreview: false,
      legacyLayout: false,
      // 三栏宽度：null 表示这一栏还用 CSS 里的默认轨道（左 300px / 右 1fr），
      // 拖动过一次就钉成固定像素值，中栏吃掉剩余空间
      workspaceColumns: { left: null, right: null },
      // 实际渲染用的宽度：窗口放得下时就等于 workspaceColumns，放不下才按比例收窄。
      // 和上面分开，是为了窗口重新变宽后能还原用户自己拖出来的宽度
      appliedColumns: { left: null, right: null },
      // 拖动中的临时状态：起始指针位置、起始栏宽、可用总宽，仅拖动期间存在
      resizeState: null,
      showLetterFormatter: false,
      letterFormatBackup: null,
      localStorageItems: ['text', 'fontFile', 'fontSize', 'lineSpacing', 'fill', 'width', 'height', 'marginTop', 'marginBottom', 'marginLeft', 'marginRight', 'selectedFontFileName', 'selectedOption', 'lineSpacingSigma', 'fontSizeSigma', 'wordSpacingSigma', 'perturbXSigma', 'perturbYSigma', 'perturbThetaSigma', 'wordSpacing', 'strikethrough_length_sigma', 'strikethrough_angle_sigma', 'strikethrough_width_sigma', 'strikethrough_probability', 'strikethrough_width', 'ink_depth_sigma', 'isUnderlined', 'enableEnglishSpacing'],
      // 这些项在 created() 里统一从 localStorage 还原。
      // workspaceColumns 没有配 watcher：拖动过程中每帧都写一次不值得，改成收手时才落盘
      persistentUiItems: ['enableFullPreview', 'legacyLayout', 'workspaceColumns'],
    };
  },
  created() {
    window.addEventListener('handwriting-text-loaded', this.onTextLoaded);

    const savedPreset = localStorage.getItem('selectedPreset');
    if (savedPreset !== null && savedPreset !== "undefined") {
      try {
        const presetKey = JSON.parse(savedPreset);
        if (typeof presetKey === 'string' && (!presetKey || this.builtinPresets[presetKey])) {
          this.selectedPreset = presetKey;
        } else {
          localStorage.removeItem('selectedPreset');
        }
      } catch (error) {
        console.error('解析内置预设失败:', error);
        localStorage.removeItem('selectedPreset');
      }
    }

    // const localStorageItems = ['text', 'fontFile', 'fontSize', 'lineSpacing', 'fill', 'width', 'height', 'marginTop', 'marginBottom', 'marginLeft', 'marginRight', 'selectedFontFileName', 'selectedOption', 'lineSpacingSigma', 'fontSizeSigma', 'wordSpacingSigma', 'perturbXSigma', 'perturbYSigma', 'perturbThetaSigma', 'wordSpacing'];//, 'backgroundImage', 'selectedImageFileName'

    [...this.localStorageItems, ...this.persistentUiItems].forEach(item => {
      const value = localStorage.getItem(item);
      if (value !== null && value !== "undefined") {
        try {
          this[item] = JSON.parse(value);
          console.log('成功加载localStorage项目:', item, '值:', this[item]);
        } catch (error) {
          console.error('解析localStorage项目失败:', item, '原始值:', value, '错误:', error);
        }
      } else {
        console.log('localstorage缺失item:' + item)
      }
    });

    if (typeof this.enableFullPreview !== 'boolean') {
      this.enableFullPreview = false;
    }

    // 存档损坏（比如被别的版本写成了字符串）时退回默认布局，别让 NaN 进 CSS
    const savedColumns = this.workspaceColumns;
    const readColumn = (value) =>
      typeof value === 'number' && Number.isFinite(value) && value > 0 ? Math.round(value) : null;
    this.workspaceColumns = {
      left: readColumn(savedColumns && savedColumns.left),
      right: readColumn(savedColumns && savedColumns.right),
    };
    this.appliedColumns = { ...this.workspaceColumns };

    this.$http.get('/api/version').then(response => {
      this.appVersion = response.data?.version || '';
    }).catch(() => {
      // 版本号只是展示信息，取不到就不显示，不打扰用户
      this.appVersion = '';
    });

    this.$http.get('/api/fonts_info').then(response => {
      this.options = response.data.map((font, index) => {
        return { value: String(index + 1), text: font };
      });
      const selected = this.builtinPresets[this.selectedPreset];
      if (selected && !this.applyPresetFont(selected.fontName)) {
        this.clearSelectedPreset();
      }
    }).catch(error => {
      if (error.response && error.response.data) {
        this.errorMessage = error.response.data.error;
        this.message = '';
        this.uploadMessage = '';
      } else {
        this.errorMessage = error;
        this.message = '';
        this.uploadMessage = '';
      }
    });
    console.log('options' + this.options)
  },
  computed: {
    isDimensionSpecified() {
      // 当宽度或高度有值时，返回 true，这会禁用背景图片输入框
      return !!(this.width || this.height);
    },
    isBackgroundImageSpecified() {
      // 当有背景图片时，返回 true，这会禁用宽度和高度输入框
      return !!this.backgroundImage;
    },

    // 拖动过的栏宽以 CSS 变量喂给 .workspace 的 grid-template-columns；
    // 没拖动过就不写变量，由 CSS 里的默认轨道接管
    workspaceStyle() {
      const style = {};
      const { left, right } = this.appliedColumns;
      if (left) style['--col-left'] = `${left}px`;
      if (right) style['--col-right'] = `${right}px`;
      return style;
    },

    // 按钮是否应该被禁用
    shouldDisableButtons() {
      // 字体列表还没回来时不能点：请求里要取 options[selectedOption - 1].text
      if (!Array.isArray(this.options) || this.options.length === 0) return true;
      return this.isGenerating || this.isInCooldownPeriod || this.queueFullCountdown > 0;
    },

    // 队列满进度条（从100%倒减到0%）
    queueFullBarPercent() {
      if (this.queueFullTotal <= 0) return 0;
      return Math.max(0, (this.queueFullCountdown / this.queueFullTotal) * 100);
    },

    // 按钮显示文本
    buttonText() {
      if (this.isGenerating) {
        return '生成中...';
      } else if (this.isInCooldownPeriod) {
        return `请等待 ${this.remainingCooldown}s`;
      }
      return null; // 使用默认文本
    },
    isDevEnv() {
      return process.env.NODE_ENV === 'development';
    },
    // 页数提示只在生产站点显示；用 computed 避免模板里反复调用 estimatePageCount()
    estimatedPages() {
      if (!this.isProductionSite() || !this.text || this.text.length === 0) {
        return 0;
      }
      return this.estimatePageCount();
    },
    presetOptionsReady() {
      const preset = this.builtinPresets.smallUnderlined;
      return Array.isArray(this.options) && this.options.some(option => option.text === preset.fontName);
    },

    //vuex中的login_delete_message，下面使用watch监控这个值  7.13
    ...mapState(['login_delete_message']),
  },
  watch: {
    login_delete_message(newVal) {
      if (newVal) {
        // this.message = '';
        // this.uploadMessage = '';
        console.log('已进入watch，错误消息已经清空');
      }
    },
    errorMessage(newVal) {
      if (newVal) {
        this.$swal.fire({
          ...this.toastBase(),
          icon: 'error',
          title: newVal,
          timer: 5000,
          timerProgressBar: true,
        });
      }
    },
    message(newVal) {
      if (newVal) {
        this.$swal.fire({
          ...this.toastBase(),
          icon: 'success',
          title: newVal,
          timer: 3000,
          timerProgressBar: true,
        });
      }
    },
    uploadMessage(newVal) {
      if (newVal) {
        this.$swal.fire({
          ...this.toastBase(),
          icon: 'info',
          title: newVal,
          timer: false, // 上传提示保持显示
          showClass: { popup: 'swal2-show' },
          hideClass: { popup: 'swal2-hide' },
        });
      }
    },
    queueFullCountdown(newVal) {
      if (newVal > 0) {
        this.$swal.fire({
          ...this.toastBase((toast) => {
            const progressBar = toast.querySelector('.swal2-timer-progress-bar');
            if (progressBar && this.queueFullTotal > 0) {
              // 更新进度条
              const updateProgress = () => {
                if (this.queueFullCountdown > 0 && progressBar) {
                  const percent = (this.queueFullCountdown / this.queueFullTotal) * 100;
                  progressBar.style.width = percent + '%';
                  requestAnimationFrame(updateProgress);
                }
              };
              requestAnimationFrame(updateProgress);
            }
          }),
          icon: 'warning',
          title: `服务器繁忙，队列已满，预计 ${newVal} 秒后可重试`,
          timer: newVal * 1000,
          timerProgressBar: true,
        });
      }
    },
    text: {
      handler(newVal) {
        localStorage.setItem('text', JSON.stringify(newVal));
      },
      deep: true
    },
    fontFile: {
      handler(newVal) {
        localStorage.setItem('fontFile', JSON.stringify(newVal));
      },
      deep: true
    },
    // backgroundImage: {
    //   handler(newVal) {
    //     localStorage.setItem('backgroundImage', JSON.stringify(newVal));
    //   },
    //   deep: true
    // },
    fontSize: {
      handler(newVal) {
        localStorage.setItem('fontSize', JSON.stringify(newVal));
      },
      deep: true
    },
    lineSpacing: {
      handler(newVal) {
        localStorage.setItem('lineSpacing', JSON.stringify(newVal));
      },
      deep: true
    },
    fill: {
      handler(newVal) {
        localStorage.setItem('fill', JSON.stringify(newVal));
      },
      deep: true
    },
    width: {
      handler(newVal) {
        localStorage.setItem('width', JSON.stringify(newVal));
      },
      deep: true
    },
    height: {
      handler(newVal) {
        localStorage.setItem('height', JSON.stringify(newVal));
      },
      deep: true
    },
    marginTop: {
      handler(newVal) {
        localStorage.setItem('marginTop', JSON.stringify(newVal));
      },
      deep: true
    },
    marginBottom: {
      handler(newVal) {
        localStorage.setItem('marginBottom', JSON.stringify(newVal));
      },
      deep: true
    },
    marginLeft: {
      handler(newVal) {
        localStorage.setItem('marginLeft', JSON.stringify(newVal));
      },
      deep: true
    },
    marginRight: {
      handler(newVal) {
        localStorage.setItem('marginRight', JSON.stringify(newVal));
      },
      deep: true
    },
    selectedFontFileName: {
      handler(newVal) {
        localStorage.setItem('selectedFontFileName', JSON.stringify(newVal));
      },
      deep: true
    },
    selectedImageFileName: {
      handler(newVal) {
        localStorage.setItem('selectedImageFileName', JSON.stringify(newVal));
      },
      deep: true
    },
    selectedOption: {
      handler(newVal) {
        localStorage.setItem('selectedOption', JSON.stringify(newVal));
      },
      deep: true
    },
    lineSpacingSigma: {
      handler(newVal) {
        localStorage.setItem('lineSpacingSigma', JSON.stringify(newVal));
      },
      deep: true
    },
    fontSizeSigma: {
      handler(newVal) {
        localStorage.setItem('fontSizeSigma', JSON.stringify(newVal));
      },
      deep: true
    },
    wordSpacingSigma: {
      handler(newVal) {
        localStorage.setItem('wordSpacingSigma', JSON.stringify(newVal));
      },
      deep: true
    },
    perturbXSigma: {
      handler(newVal) {
        localStorage.setItem('perturbXSigma', JSON.stringify(newVal));
      },
      deep: true
    },
    perturbYSigma: {
      handler(newVal) {
        localStorage.setItem('perturbYSigma', JSON.stringify(newVal));
      },
      deep: true
    },
    perturbThetaSigma: {
      handler(newVal) {
        localStorage.setItem('perturbThetaSigma', JSON.stringify(newVal));
      },
      deep: true
    },
    wordSpacing: {
      handler(newVal) {
        localStorage.setItem('wordSpacing', JSON.stringify(newVal));
      },
      deep: true
    },
    strikethrough_length_sigma: {
      handler(newVal) {
        localStorage.setItem('strikethrough_length_sigma', JSON.stringify(newVal));
      },
      deep: true
    },
    strikethrough_angle_sigma: {
      handler(newVal) {
        localStorage.setItem('strikethrough_angle_sigma', JSON.stringify(newVal));
      },
      deep: true
    },
    strikethrough_width_sigma: {
      handler(newVal) {
        localStorage.setItem('strikethrough_width_sigma', JSON.stringify(newVal));
      },
      deep: true
    },
    strikethrough_probability: {
      handler(newVal) {
        localStorage.setItem('strikethrough_probability', JSON.stringify(newVal));
      },
      deep: true
    },
    strikethrough_width: {
      handler(newVal) {
        localStorage.setItem('strikethrough_width', JSON.stringify(newVal));
      },
      deep: true
    },
    ink_depth_sigma: {
      handler(newVal) {
        localStorage.setItem('ink_depth_sigma', JSON.stringify(newVal));
      },
      deep: true
    },
    isUnderlined: {
      handler(newVal) {
        localStorage.setItem('isUnderlined', JSON.stringify(newVal));
      },
      deep: true
    },
    enableEnglishSpacing: {
      handler(newVal) {
        localStorage.setItem('enableEnglishSpacing', JSON.stringify(newVal));
      },
      deep: true
    },
    enableFullPreview(newVal) {
      localStorage.setItem('enableFullPreview', JSON.stringify(newVal));
    },
    legacyLayout(newVal) {
      localStorage.setItem('legacyLayout', JSON.stringify(newVal));
    },
  },

  methods: {
    openLetterFormatter() {
      if (!this.text || !this.text.trim()) {
        this.$swal.fire({
          ...this.toastBase(),
          icon: 'info',
          title: this.$t('message.letterTextRequired'),
          timer: 2200,
        });
        return;
      }
      this.showLetterFormatter = true;
    },
    // 顶栏操作按钮排在页面顶部，toast 固定在右上角会盖住按钮、吞掉点击。
    // 实测按钮行最右端约 1060px，加上 toast 自身 360px 宽，所以 1440px 以下改贴右下角。
    toastPosition() {
      return window.innerWidth <= 1440 ? 'bottom-end' : 'top-end';
    },
    // toast 的公共配置；didOpen 回调可选，用于叠加自定义逻辑（如队列满的进度条）
    toastBase(didOpen) {
      return {
        toast: true,
        position: this.toastPosition(),
        showConfirmButton: false,
        didOpen: (toast) => {
          // 供 e2e 选择，不依赖 SweetAlert 自己的类名
          toast.setAttribute('data-testid', 'app-toast');
          if (didOpen) didOpen(toast);
        },
      };
    },
    applyLetterFormatting(formattedText) {
      const textInput = this.$refs.textInputComp;
      if (!textInput || typeof textInput.replaceText !== 'function') return;

      if (this.letterFormatBackup === null) {
        this.letterFormatBackup = this.text;
      }
      textInput.replaceText(formattedText);
      this.showLetterFormatter = false;
      this.message = this.$t('message.letterFormatApplied');
    },
    undoLetterFormatting() {
      const textInput = this.$refs.textInputComp;
      if (!textInput || typeof textInput.replaceText !== 'function' || this.letterFormatBackup === null) return;

      const previousText = this.letterFormatBackup;
      this.letterFormatBackup = null;
      textInput.replaceText(previousText);
    },
    clearLetterFormatBackup() {
      this.letterFormatBackup = null;
    },
    // 文本文件上传是异步的；上传途中切换布局会重建 TextInput，旧实例的 emit 会被 Vue 丢弃，
    // 所以由 TextInput 广播事件，这里再把结果喂给当前活着的输入框（见 TextInput.uploadFile）
    onTextLoaded(event) {
      const loadedText = event.detail;
      if (typeof loadedText !== 'string') return;
      this.text = loadedText;
      const input = this.$refs.textInputComp;
      if (input && typeof input.replaceText === 'function' && input.text !== loadedText) {
        input.replaceText(loadedText);
      }
    },
    clearSelectedPreset() {
      this.selectedPreset = '';
      localStorage.removeItem('selectedPreset');
    },
    applyPresetFont(fontName) {
      if (!fontName || !Array.isArray(this.options)) return false;

      const match = this.options.find(option => option.text === fontName);
      if (!match) return false;

      this.selectedOption = match.value;
      this.fontFile = null;
      this.selectedFontFileName = '';
      if (this.$refs.fontFileInput) {
        this.$refs.fontFileInput.value = '';
      }
      localStorage.setItem('selectedOption', JSON.stringify(match.value));
      localStorage.setItem('fontFile', JSON.stringify(null));
      localStorage.setItem('selectedFontFileName', JSON.stringify(''));
      return true;
    },
    applyPreset(event) {
      const presetKey = event.target.value;
      const preset = this.builtinPresets[presetKey];
      if (!preset) {
        this.clearSelectedPreset();
        return;
      }

      if (this.backgroundImage && ('width' in preset.values || 'height' in preset.values)) {
        event.target.value = this.selectedPreset;
        this.$swal.fire({
          icon: 'info',
          title: this.$t('message.presetBackgroundImageActive'),
        });
        return;
      }

      if (!this.applyPresetFont(preset.fontName)) {
        event.target.value = this.selectedPreset;
        this.$swal.fire({
          icon: 'error',
          title: this.$t('message.presetUnavailable'),
        });
        return;
      }

      Object.entries(preset.values).forEach(([key, value]) => {
        this[key] = value;
        localStorage.setItem(key, JSON.stringify(value));
      });
      this.selectedPreset = presetKey;
      localStorage.setItem('selectedPreset', JSON.stringify(this.selectedPreset));

      this.$swal.fire({
        icon: 'success',
        title: this.$t('message.presetApplied'),
        timer: 1500,
        showConfirmButton: false,
      });
    },
    prevPage() {
      if (this.currentPreviewIndex > 0) {
        this.currentPreviewIndex--;
      }
    },
    nextPage() {
      if (this.currentPreviewIndex < this.previewImages.length - 1) {
        this.currentPreviewIndex++;
      }
    },
    toggleCollapse() {
      this.isExpanded = !this.isExpanded;
    },
    toggleFullPreview() {
      this.enableFullPreview = !this.enableFullPreview;
    },
    toggleLayout() {
      this.legacyLayout = !this.legacyLayout;
    },
    // ===== 三栏宽度调整 =====
    // 量一次工作区与左右两栏的当前尺寸。拖动开始时左右两栏会被钉成此刻的像素宽度，
    // 之后只有中栏伸缩，所以 clamp 只要守住「两栏 + 两条间隔 + 中栏最小宽度 ≤ 可用宽度」
    measureWorkspaceMetrics() {
      const workspace = this.$refs.workspace;
      if (!workspace || !this.$refs.panelSettings || !this.$refs.panelPreview) return null;
      const style = getComputedStyle(workspace);
      const padding = parseFloat(style.paddingLeft) + parseFloat(style.paddingRight);
      return {
        available: workspace.getBoundingClientRect().width - padding,
        left: this.$refs.panelSettings.getBoundingClientRect().width,
        right: this.$refs.panelPreview.getBoundingClientRect().width,
      };
    },
    // 左右两栏一起钉成固定像素宽度；中栏拿走剩下的空间。拖出来的值同时是"用户要的宽度"和"当前渲染宽度"
    applyColumnWidths(left, right) {
      const columns = { left: Math.round(left), right: Math.round(right) };
      this.workspaceColumns = columns;
      this.appliedColumns = { ...columns };
    },
    // 存储不可用（隐私模式 / 配额满）时 setItem 会抛异常。这里吞掉它，
    // 否则 resetColumnWidth 里紧跟着的那次 clamp 会被跳过，布局可能停在放不下的状态
    persistWorkspaceColumns() {
      try {
        localStorage.setItem('workspaceColumns', JSON.stringify(this.workspaceColumns));
      } catch (error) {
        console.warn('保存栏宽失败:', error);
      }
    },
    startResize(side, event) {
      const metrics = this.measureWorkspaceMetrics();
      if (!metrics) return;
      // 先把两栏都钉成当前像素宽度：中栏剩下的宽度不变（画面不跳），
      // 且拖动期间只有中栏在伸缩，上面那条 clamp 算术才成立
      this.applyColumnWidths(metrics.left, metrics.right);
      this.resizeState = {
        side,
        startX: event.clientX,
        startLeft: Math.round(metrics.left),
        startRight: Math.round(metrics.right),
        available: metrics.available,
      };
      // 指针会移出分隔条，把事件捕获到它自己身上；同时屏蔽整页的选中与光标抖动
      if (event.currentTarget.setPointerCapture) {
        event.currentTarget.setPointerCapture(event.pointerId);
      }
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
    },
    onResizeMove(event) {
      const state = this.resizeState;
      if (!state) return;
      const delta = event.clientX - state.startX;
      // 另一栏此刻是钉死的，中栏最小宽度要从可用宽度里扣掉它
      const otherWidth = state.side === 'left' ? state.startRight : state.startLeft;
      const maxSide = state.available - GUTTER_WIDTH * 2 - MIN_MIDDLE_WIDTH - otherWidth;
      if (state.side === 'left') {
        const left = clamp(state.startLeft + delta, MIN_COLUMN_WIDTH, Math.max(MIN_COLUMN_WIDTH, maxSide));
        this.applyColumnWidths(left, state.startRight);
      } else {
        const right = clamp(state.startRight - delta, MIN_COLUMN_WIDTH, Math.max(MIN_COLUMN_WIDTH, maxSide));
        this.applyColumnWidths(state.startLeft, right);
      }
    },
    endResize(event) {
      if (!this.resizeState) return;
      if (event.currentTarget.releasePointerCapture && event.currentTarget.hasPointerCapture
        && event.currentTarget.hasPointerCapture(event.pointerId)) {
        event.currentTarget.releasePointerCapture(event.pointerId);
      }
      this.resizeState = null;
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
      this.persistWorkspaceColumns();
    },
    // 双击分隔条：这一栏退回 CSS 的弹性默认宽度（左 300px / 右 1fr）
    resetColumnWidth(side) {
      const columns = { ...this.workspaceColumns, [side]: null };
      this.workspaceColumns = columns;
      this.appliedColumns = { ...columns };
      this.persistWorkspaceColumns();
      // 另一栏还钉着的话，退回弹性列后可能放不下，按当前窗口再收一次
      this.clampWorkspaceColumns();
    },
    onResizerKeydown(side, event) {
      // 方向键朝着分隔条该走的方向推：左分隔条按 → 加宽左栏，右分隔条按 ← 加宽右栏
      const growKey = side === 'left' ? 'ArrowRight' : 'ArrowLeft';
      const shrinkKey = side === 'left' ? 'ArrowLeft' : 'ArrowRight';
      if (event.key !== growKey && event.key !== shrinkKey) return;
      event.preventDefault();

      const metrics = this.measureWorkspaceMetrics();
      if (!metrics) return;
      const other = side === 'left' ? metrics.right : metrics.left;
      const current = side === 'left' ? metrics.left : metrics.right;
      const maxSide = metrics.available - GUTTER_WIDTH * 2 - MIN_MIDDLE_WIDTH - other;
      const step = event.key === growKey ? KEYBOARD_RESIZE_STEP : -KEYBOARD_RESIZE_STEP;
      const next = clamp(current + step, MIN_COLUMN_WIDTH, Math.max(MIN_COLUMN_WIDTH, maxSide));

      // 键盘调整也把两栏一起钉住，否则中栏的伸缩比例会和拖动时对不上
      this.applyColumnWidths(side === 'left' ? next : metrics.left, side === 'right' ? next : metrics.right);
      this.persistWorkspaceColumns();
    },
    // 窗口变窄时把渲染宽度按比例收回来，否则左右两栏会把中栏挤到最小宽度以下、整页横向溢出。
    // 只改 appliedColumns，用户拖出来的值留在 workspaceColumns 里，窗口重新变宽时能还回去
    clampWorkspaceColumns() {
      const { left, right } = this.workspaceColumns;
      if (!left && !right) return;
      const workspace = this.$refs.workspace;
      if (!workspace) return;
      // 窄屏是单栏堆叠，栏宽存的是宽屏时的值，这时候不能拿当前宽度去压它
      const settings = this.$refs.panelSettings.getBoundingClientRect();
      const preview = this.$refs.panelPreview.getBoundingClientRect();
      if (preview.left < settings.right) return;

      const metrics = this.measureWorkspaceMetrics();
      if (!metrics) return;
      // 没钉住的那一栏按 CSS 默认轨道渲染，但占的宽度也要算进来
      const currentLeft = left || metrics.left;
      const currentRight = right || metrics.right;
      const maxTotal = metrics.available - GUTTER_WIDTH * 2 - MIN_MIDDLE_WIDTH;
      if (currentLeft + currentRight <= maxTotal) {
        this.appliedColumns = { left, right };
        return;
      }

      const scale = maxTotal / (currentLeft + currentRight);
      let nextLeft = Math.max(MIN_COLUMN_WIDTH, Math.round(currentLeft * scale));
      let nextRight = Math.max(MIN_COLUMN_WIDTH, Math.round(currentRight * scale));
      // 两侧各自有 200px 下限，按比例缩完再抬到下限后可能仍超预算，多出来的从较宽的一侧扣掉
      const excess = nextLeft + nextRight - maxTotal;
      if (excess > 0) {
        if (nextLeft > nextRight) {
          nextLeft -= excess;
        } else {
          nextRight -= excess;
        }
      }
      this.appliedColumns = { left: nextLeft, right: nextRight };
    },
    startQueueFullCountdown(seconds) {
      // 清掉旧计时器
      if (this.queueFullTimer) {
        clearInterval(this.queueFullTimer);
        this.queueFullTimer = null;
      }
      this.queueFullTotal = seconds;
      this.queueFullCountdown = seconds;
      this.queueFullTimer = setInterval(() => {
        this.queueFullCountdown -= 1;
        if (this.queueFullCountdown <= 0) {
          this.queueFullCountdown = 0;
          clearInterval(this.queueFullTimer);
          this.queueFullTimer = null;
        }
      }, 1000);
    },
    updateTaskUploadMessage(taskData, taskId) {
      const taskStatus = taskData?.task_status;
      const taskMessage = taskData?.task_message || '任务处理中';
      const taskProgress = taskData?.task_progress;
      const queuePendingCount = taskData?.queue_pending_count;
      const queueAheadCount = taskData?.queue_ahead_count;
      const processingCount = taskData?.processing_count;
      if (taskStatus === 'pending' && typeof queuePendingCount === 'number' && typeof queueAheadCount === 'number') {
        if (typeof processingCount === 'number') {
          this.uploadMessage = `${taskMessage}（前方排队 ${queueAheadCount} 人，当前排队 ${queuePendingCount} 人，处理中 ${processingCount} 人） Task ID: ${taskId}`;
        } else {
          this.uploadMessage = `${taskMessage}（前方排队 ${queueAheadCount} 人，当前排队 ${queuePendingCount} 人） Task ID: ${taskId}`;
        }
      } else if (typeof taskProgress === 'number') {
        this.uploadMessage = `${taskMessage}（${taskProgress}%） Task ID: ${taskId}`;
      } else {
        this.uploadMessage = `${taskMessage} Task ID: ${taskId}`;
      }
    },
    async waitForTaskViaWebSocket(taskId, timeoutMs = 5 * 60 * 1000) {
      return new Promise((resolve, reject) => {
        let isSettled = false;
        const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
        const wsUrl = `${protocol}://${window.location.host}/api/generate_handwriting/ws/${taskId}`;
        const socket = new WebSocket(wsUrl);

        const timeoutId = setTimeout(() => {
          if (isSettled) return;
          isSettled = true;
          try {
            socket.close();
          } catch (e) {
            // ignore close errors
          }
          reject(new Error('WebSocket任务等待超时'));
        }, timeoutMs);

        socket.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data?.status === 'error') {
              if (isSettled) return;
              isSettled = true;
              clearTimeout(timeoutId);
              socket.close();
              reject(new Error(data?.message || '任务不存在'));
              return;
            }

            this.updateTaskUploadMessage(data, taskId);
            if (data?.task_status === 'completed') {
              if (isSettled) return;
              isSettled = true;
              clearTimeout(timeoutId);
              socket.close();
              resolve();
            } else if (data?.task_status === 'failed') {
              if (isSettled) return;
              isSettled = true;
              clearTimeout(timeoutId);
              socket.close();
              reject(new Error(data?.error_message || '任务执行失败'));
            }
          } catch (e) {
            // ignore malformed payload
          }
        };

        socket.onerror = () => {
          if (isSettled) return;
          isSettled = true;
          clearTimeout(timeoutId);
          reject(new Error('WebSocket连接失败'));
        };

        socket.onclose = () => {
          if (isSettled) return;
          isSettled = true;
          clearTimeout(timeoutId);
          reject(new Error('WebSocket连接已关闭'));
        };
      });
    },
    async pollGenerationTask(taskId, timeoutMs = 5 * 60 * 1000, intervalMs = 1500) {
      const start = Date.now();
      while (Date.now() - start < timeoutMs) {
        const statusResponse = await this.$http.get(`/api/generate_handwriting/task/${taskId}`);
        const taskStatus = statusResponse.data?.task_status;
        this.updateTaskUploadMessage(statusResponse.data, taskId);
        if (taskStatus === 'completed') {
          return;
        }
        if (taskStatus === 'failed') {
          throw new Error(statusResponse.data?.error_message || '任务执行失败');
        }
        await new Promise(resolve => setTimeout(resolve, intervalMs));
      }
      throw new Error('任务处理超时，请重试');
    },
    handleGenerationResultResponse(response) {
      const contentType = response.headers['content-type'] || '';
      if (contentType.includes('application/json')) {
        // 处理多页预览图像 (JSON)
        if (response.data && response.data.status === 'success') {
          this.previewImages = response.data.images.map(img => 'data:image/png;base64,' + img);
          this.currentPreviewIndex = 0; // 重置为第一页
          if (this.previewImages.length > 0) {
            this.previewImage = this.previewImages[0]; // 兼容显示第一页
          }
          this.message = '预览图像已加载。';
          this.uploadMessage = '';
          this.errorMessage = '';
        }
      } else if (contentType.includes('image/png')) {
        // 兼容旧的单张图片返回逻辑
        const blobUrl = URL.createObjectURL(response.data);
        // 将预览图像的 URL 保存到数据属性中
        this.previewImage = blobUrl;
        this.previewImages = [blobUrl];
        // 设置提示信息
        this.message = '预览图像已加载。';//显示message时，隐藏其他提示信息
        this.uploadMessage = '';
        this.errorMessage = '';

      } else if (contentType.includes('application/zip')) {
        // 处理.zip文件
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', 'images.zip'); // 或任何其他文件名
        document.body.appendChild(link);
        link.click();
        // 下载完成后，将链接删除，7.5
        document.body.removeChild(link);
        // 设置提示信息
        this.message = '文件已下载。';
        this.uploadMessage = '';
        this.errorMessage = '';

      } else if (contentType.includes('application/pdf')) {
        // 处理.pdf文件
        const pdfBlob = new Blob([response.data], { type: 'application/pdf' });
        const url = window.URL.createObjectURL(pdfBlob);
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', 'images.pdf'); // 或任何其他文件名
        document.body.appendChild(link);
        link.click();
        // 下载完成后，将链接删除
        document.body.removeChild(link);
        // e2e 靠这个数字核对实际交付的 PDF 体积（见 e2e/tests/home-generate.spec.js）
        this.lastPdfDownloadBytes = pdfBlob.size;
        // 设置提示信息
        this.message = '文件已下载。';
        this.uploadMessage = '';
        this.errorMessage = '';
      } else {
        // console.log(text);
        console.error(`Unexpected response type: ${contentType}, ${response.data}`);
      }
    },
    async generateHandwriting(preview = false, pdf_save = false) {
      // console.log('pdf_save', pdf_save)

      // 检查是否正在生成
      if (this.isGenerating) {
        this.$swal.fire({
          icon: 'warning',
          title: '正在生成中，请稍候...',
          showConfirmButton: false,
          timer: 2000,
        });
        return;
      }

      // 检查冷却时间
      const currentTime = Date.now();
      const timeSinceLastGenerate = currentTime - this.lastGenerateTime;
      if (timeSinceLastGenerate < this.generateCooldown) {
        const remainingTime = Math.ceil((this.generateCooldown - timeSinceLastGenerate) / 1000);
        this.$swal.fire({
          icon: 'warning',
          title: `请等待 ${remainingTime} 秒后再次生成`,
          showConfirmButton: false,
          timer: 2000,
        });
        return;
      }

      // 设置生成状态
      this.isGenerating = true;
      this.lastGenerateTime = currentTime;

      // 启动冷却时间定时器
      this.startCooldownTimer();

      try {
        // 检查是否为生产环境并进行页数限制
        if (!preview && this.isProductionSite()) {
          const estimatedPages = this.estimatePageCount();
          if (estimatedPages > 15) {
            const confirmed = await this.showPageLimitDialog(estimatedPages);
            if (!confirmed) {
              return; // 用户取消生成
            }
            // 用户确认继续，在前端截断文本到前15页
            this.truncateTextToPages(15);
          }
        }

      // 验证输入
      const Items = ['text', 'backgroundImage', 'fontSize', 'lineSpacing', 'marginTop', 'marginBottom', 'marginLeft', 'marginRight', 'lineSpacingSigma', 'fontSizeSigma', 'wordSpacingSigma', 'perturbXSigma', 'perturbYSigma', 'perturbThetaSigma', 'wordSpacing', 'strikethrough_length_sigma', 'strikethrough_angle_sigma', 'strikethrough_width_sigma', 'strikethrough_probability', 'strikethrough_width', 'ink_depth_sigma'];
      Items.forEach(item => {
        let value = this[item];
        // if (!value) {
        //   console.error(`Missing value for ${item}`);
        //   return;
        // }
        // 对不同的输入进行不同的验证
        switch (item) {
          case 'text':
            // 验证 text 是否是字符串
            if (typeof value !== 'string') {
              console.error(`Invalid value for ${item}`);
              this.errorMessage = '请输入字符串';
            }
            // return;
            break;
          case 'fontSize':
          case 'lineSpacing':
          case 'marginTop':
          case 'marginBottom':
          case 'marginLeft':
          case 'marginRight':
          case 'lineSpacingSigma':
          case 'fontSizeSigma':
          case 'wordSpacingSigma':
          case 'perturbXSigma':
          case 'perturbYSigma':
          case 'perturbThetaSigma':
          case 'wordSpacing':
          case 'strikethrough_length_sigma':
          case 'strikethrough_angle_sigma':
          case 'strikethrough_width_sigma':
          case 'strikethrough_probability':
          case 'strikethrough_width':
          case 'ink_depth_sigma':
            // 验证这些值是否是数字
            if (isNaN(Number(value))) {
              console.error(`Invalid value for ${item}`);
              this.errorMessage = '请输入数字';
            }
            // return
            break;
          case 'backgroundImage':
            // 验证 backgroundImage 是否是有效的 URL 或者文件路径
            // 这可能需要更复杂的验证
            break;
          default:
            console.error(`Unknown item: ${item}`);
        }
      });

      if (this.height < this.marginTop + this.lineSpacing + this.marginBottom && this.isDimensionSpecified) {
        this.errorMessage = '上边距、下边距和行间距之和不能大于高度';
        this.message = '';
        this.uploadMessage = '';
        return;
      }
      if (this.fontSize > this.lineSpacing) {
        this.errorMessage = '字体大小不能大于行间距';
        this.message = '';
        this.uploadMessage = '';
        return;
      }

      this.preview = preview;
      // this.pdf_save = pdf_save;
      // 设置提示信息为“内容正在上传…”
      this.uploadMessage = '内容正在上传并处理…（如果长时间没有响应说明服务器崩溃）单次请求最多处理五分钟，超过这个时间则失败';//显示上传提示信息时，隐藏其他提示信息
      console.log('内容正在上传并处理…');
      this.message = '';
      this.errorMessage = '';
      const formData = new FormData();
      formData.append("text", this.text);
      // 只有当用户选择的字体文件名与字体下拉选项中的字体文件名相同时，才上传字体文件7.5
      if (this.options[this.selectedOption - 1].text == this.selectedFontFileName) {
        formData.append("font_file", this.fontFile);
      }
      formData.append("background_image", this.backgroundImage);
      formData.append("font_size", this.fontSize);
      formData.append("line_spacing", this.lineSpacing);
      formData.append("fill", this.fill);
      if (this.width) {
        formData.append("width", this.width);
      }
      if (this.height) {
        formData.append("height", this.height);
      }
      formData.append("top_margin", this.marginTop);
      formData.append("bottom_margin", this.marginBottom);
      formData.append("left_margin", this.marginLeft);
      formData.append("right_margin", this.marginRight);
      formData.append("line_spacing_sigma", this.lineSpacingSigma);
      formData.append("font_size_sigma", this.fontSizeSigma);
      formData.append("word_spacing_sigma", this.wordSpacingSigma);
      formData.append("end_chars", this.endChars);
      formData.append("perturb_x_sigma", this.perturbXSigma);
      formData.append("perturb_y_sigma", this.perturbYSigma);
      formData.append("perturb_theta_sigma", this.perturbThetaSigma);
      formData.append("word_spacing", this.wordSpacing);
      formData.append("preview", this.preview.toString());
      formData.append("font_option", this.options[this.selectedOption - 1].text);
      formData.append("strikethrough_length_sigma", this.strikethrough_length_sigma);
      formData.append("strikethrough_angle_sigma", this.strikethrough_angle_sigma);
      formData.append("strikethrough_width_sigma", this.strikethrough_width_sigma);
      formData.append("strikethrough_probability", this.strikethrough_probability);
      formData.append("strikethrough_width", this.strikethrough_width);
      formData.append("ink_depth_sigma", this.ink_depth_sigma);
      formData.append("pdf_save", pdf_save.toString());
      formData.append("isUnderlined", this.isUnderlined.toString());
      formData.append("enableEnglishSpacing", this.enableEnglishSpacing.toString());
      
      // 根据环境与按钮决定是否启用多页预览
      const isDevEnv = process.env.NODE_ENV === 'development';
      const allowFullPreview = isDevEnv && this.enableFullPreview && preview;
      formData.append("full_preview", allowFullPreview.toString());

      for (let pair of formData.entries()) {
        console.log(pair[0] + ', ' + pair[1]);
      }

      const taskCreateResponse = await this.$http.post(
        '/api/generate_handwriting',
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
          withCredentials: true, //在跨域的时候，需要添加这句话，才能发送cookie 6.30
        }
      );

      const taskId = taskCreateResponse.data?.task_id;
      if (!taskId) {
        throw new Error('未获取到任务ID');
      }

      this.uploadMessage = `任务已提交，正在生成中（Task ID: ${taskId}）…`;
      try {
        await this.waitForTaskViaWebSocket(taskId);
      } catch (wsError) {
        console.warn('WebSocket不可用，降级为轮询模式', wsError);
        await this.pollGenerationTask(taskId);
      }

      const resultResponse = await this.$http.get(
        `/api/generate_handwriting/task/${taskId}/result`,
        {
          // 预览模式下：开发环境使用json接收多页图片，生产环境使用blob接收单页图片
          responseType: preview ? (allowFullPreview ? 'json' : 'blob') : 'blob',
          withCredentials: true,
        }
      );
      this.handleGenerationResultResponse(resultResponse);
      } catch (error) {
        if (error.response) {
          // ── 队列已满：503 queue_full ────────────────────────────────
          const errData = error.response.data;
          if (
            error.response.status === 503 &&
            errData?.status === 'queue_full'
          ) {
            const waitSec = errData.estimated_wait_seconds || 30;
            this.startQueueFullCountdown(waitSec);
            this.message = '';
            this.uploadMessage = '';
            this.errorMessage = '';
            return; // 不走通用错误展示
          }
          // ────────────────────────────────────────────────────────────
          // console.log('已进入报错处理程序')
          // 如果服务器返回了一个JSON错误消息
          if (error.response.data instanceof Blob) {
            let reader = new FileReader();
            reader.onload = (e) => {
              try {
                let errorData = JSON.parse(e.target.result);
                this.errorMessage = errorData.message;
              } catch (parseError) {
                // 如果解析失败，直接显示原始信息
                this.errorMessage = e.target.result;
                console.log('非JSON格式的错误数据：', e.target.result);
              }
              this.message = '';
              this.uploadMessage = '';
              console.log('错误信息：', this.errorMessage);
              console.log(error);
            };//注意，这里只能使用箭头函数，不然this指向全局对象window，6.30
            reader.readAsText(error.response.data);
          } else {
            this.errorMessage = error.response.data?.message || '生成失败，请稍后重试';
            // this.errorMessage = error.response.data.message;
            this.message = '';
            this.uploadMessage = '';
          }
        } else {
          // 如果没有从服务器收到响应
          this.errorMessage = error.message || '网络错误，请稍后再试';
          this.message = '';
          this.uploadMessage = '';
        }
      } finally {
        // 重置生成状态，但保持冷却状态
        this.isGenerating = false;
        // 冷却定时器会自动处理冷却状态的重置
      }
    },
    savePreset() {
      try {
        let data = {};
        this.localStorageItems.forEach(item => {
          data[item] = this[item];
        });
        // 将对象转换为 JSON 格式的字符串
        let dataString = JSON.stringify(data);

        // 将字符串存储到 localStorage 中
        localStorage.setItem('myPreset', dataString);

        this.$swal.fire({
          icon: 'success',
          title: '预设设置保存成功！',
          timer: 2000,
          showConfirmButton: false,
        });
      } catch (error) {
        console.error('保存预设设置失败:', error);
        this.$swal.fire({
          icon: 'error',
          title: '保存预设设置失败',
        });
      }
    },
    resetSettings() {
      // this.text = '';13213不能删除，会导致文字为空，但是输入框没有清除
      this.fontFile = null;
      this.backgroundImage = null;
      this.fontSize = 124;
      this.lineSpacing = 200;
      this.fill = "(0, 0, 0, 255)";
      this.width = 2481;
      this.height = 3507;
      this.marginTop = 50;
      this.marginBottom = 50;
      this.marginLeft = 50;
      this.marginRight = 50;
      this.lineSpacingSigma = 0;
      this.fontSizeSigma = 2;
      this.wordSpacingSigma = 2;
      this.perturbXSigma = 3;
      this.perturbYSigma = 3;
      this.perturbThetaSigma = 0.05;
      this.wordSpacing = 1;
      this.strikethrough_length_sigma = 2;
      this.strikethrough_angle_sigma = 2;
      this.strikethrough_width_sigma = 2;
      this.strikethrough_probability = 0.005;
      this.strikethrough_width = 8;
      this.ink_depth_sigma = 30;
      this.isUnderlined = true;
      this.enableEnglishSpacing = false;
      this.errorMessage = '';
      this.message = '';
      this.uploadMessage = '';
      this.selectedFontFileName = '';
      this.selectedImageFileName = '';
      this.selectedOption = '1';
      this.clearSelectedPreset();
      this.previewImage = "/default1.webp";
    },
    loadPreset() {
      try {
        // 从 localStorage 中获取字符串
        let dataString = localStorage.getItem('myPreset');

        if (dataString === null || dataString === "undefined") {
          this.$swal.fire({
            icon: 'info',
            title: '没有找到保存的预设设置',
          });
          return;
        }

        // 将字符串转换回对象
        let data = JSON.parse(dataString);
        Object.keys(data).forEach(item => {
          this[item] = data[item];
        });
        this.clearSelectedPreset();

        this.$swal.fire({
          icon: 'success',
          title: '预设设置加载成功！',
          timer: 2000,
          showConfirmButton: false,
        });
      } catch (error) {
        console.error('加载预设设置失败:', error);
        this.$swal.fire({
          icon: 'error',
          title: '加载预设设置失败，请检查保存的数据是否有效',
        });
      }
    },
    onBackgroundImageChange(event) {
      this.clearSelectedPreset();
      // 当用户选择了一个新的背景图片文件时，更新 selectedImageFileName，由于这边直接触发函数了，所以localstorage可以在这里修改，
      //之前因为文字不能触发函数，所以要放在watch里面
      this.selectedImageFileName = event.target.files[0].name;
      this.backgroundImage = event.target.files[0];
      // 由于文件无法在浏览器存储，所以下面的代码无效 7.15
      // localStorage.setItem('backgroundImage', JSON.stringify(this.backgroundImage));
      // if (localStorage.getItem('backgroundImage')) {
      //   console.log('Data successfully saved to localStorage.');
      // } else {
      //   console.log('Failed to save to localStorage.');
      // }

      this.previewImage = URL.createObjectURL(event.target.files[0]);
      Swal.fire({
        title: '你希望自动识别页面的四周边距吗？（尽量不要上传带有alpha透明通道的图片）',
        icon: 'question',
        showCancelButton: true,
        confirmButtonText: '确定',
        cancelButtonText: '取消'
      }).then((result) => {
        if (result.isConfirmed) {
          let formData = new FormData();
          formData.append('file', this.backgroundImage);  // 'file' 是你在服务器端获取文件数据时的 key
          this.isLoading = true;
          this.$http.post(
            '/api/imagefileprocess',
            formData, {
            headers: {
              'Content-Type': 'multipart/form-data'
            }
          })
            .then(response => {
              this.marginLeft = response.data.marginLeft;
              this.marginRight = response.data.marginRight;
              this.marginTop = response.data.marginTop - this.lineSpacing;
              this.marginBottom = response.data.marginBottom;
              this.lineSpacing = response.data.lineSpacing;
              this.message = '背景图片已加载。';
              this.errorMessage = '';
              this.uploadMessage = '';
              this.isLoading = false;
            })
            .catch(error => {
              console.error(error);
              this.errorMessage = error.response.data.error;
              this.message = '';
              this.uploadMessage = '';
              this.isLoading = false;
            });
        }
      })
    },
    onFontChange(event) {
      this.clearSelectedPreset();
      // 当用户选择了一个新的字体文件时，更新 selectedFontFileName
      this.selectedFontFileName = event.target.files[0].name;
      this.fontFile = event.target.files[0];
      // 创建一个新的 option 对象
      const newOption = {
        value: String(this.options.length + 1), // 使用 options 数组的长度 + 1 作为新选项的 value
        text: this.selectedFontFileName // 使用字体文件名作为新选项的 text
      };

      // 将新选项添加到 options 数组中
      this.options.push(newOption);

      // 将 selectedOption 设为新选项的 value，这样下拉菜单就会自动更新为新添加的字体
      this.selectedOption = newOption.value;

    },
    triggerImageFileInput() {
      if (!this.isDimensionSpecified) {
        this.$refs.imageFileInput.click();
      }
      else {
        Swal.fire({
          title: '需要先清空高度宽度才能选择图片',
          text: '选择图片后需要点击按钮左下角的X删除图片才能再输入宽度高度',
          icon: 'question',
          showCancelButton: true,
          confirmButtonText: '清空宽度高度',
          cancelButtonText: '取消'
        }).then((result) => {
          if (result.isConfirmed) {
            this.width = null
            this.height = null
            this.$refs.imageFileInput.click();
          }
        })
      }
    },
    triggerFontFileInput() {
      this.$refs.fontFileInput.click();
    },
    //清空图像按钮对应的函数
    clearImage() {
      // 清空存储图像信息的变量
      this.selectedImageFileName = null;
      this.backgroundImage = null;
      // 清空文件输入框
      this.$refs.imageFileInput.value = null;
    },
    clearDimensions() {
      console.log('清空图像尺寸');
      this.width = null
      this.height = null
    },

    // 检查是否为生产网站
    isProductionSite() { // localhost:8080 handwrite.14790897.xyz
      return window.location.hostname === 'handwrite.14790897.xyz';
    },

    // 估算页数
    estimatePageCount() {
      if (!this.text || this.text.length === 0) {
        return 0;
      }

      // 获取页面参数
      const pageWidth = this.width || (this.backgroundImage ? 2481 : 2481); // 默认宽度
      const pageHeight = this.height || (this.backgroundImage ? 3507 : 3507); // 默认高度
      const fontSize = parseInt(this.fontSize) || 20;
      const lineSpacing = parseInt(this.lineSpacing) || 30;
      const marginTop = parseInt(this.marginTop) || 50;
      const marginBottom = parseInt(this.marginBottom) || 50;
      const marginLeft = parseInt(this.marginLeft) || 50;
      const marginRight = parseInt(this.marginRight) || 50;

      // 计算可用区域
      const usableWidth = pageWidth - marginLeft - marginRight;
      const usableHeight = pageHeight - marginTop - marginBottom;

      // 估算每行字符数（粗略估算，中文字符按字体大小计算）
      const avgCharWidth = fontSize * 0.8; // 中文字符宽度约为字体大小的0.8倍
      const charsPerLine = Math.floor(usableWidth / avgCharWidth);

      // 估算每页行数
      const linesPerPage = Math.floor(usableHeight / lineSpacing);

      // 估算每页字符数
      const charsPerPage = charsPerLine * linesPerPage;

      // 计算页数
      const estimatedPages = Math.ceil(this.text.length / charsPerPage);

      console.log('页数估算:', {
        textLength: this.text.length,
        charsPerLine,
        linesPerPage,
        charsPerPage,
        estimatedPages
      });

      return estimatedPages;
    },

    // 显示页数限制对话框
    async showPageLimitDialog(estimatedPages) {
      try {
        const result = await this.$swal.fire({
          title: '页数限制提醒',
          html: `
            <div style="text-align: left; line-height: 1.6;">
              <p><strong>检测到您的文本预计会生成 ${estimatedPages} 页</strong></p>
              <p>由于服务器资源限制，在 <strong>handwrite.14790897.xyz</strong> 网站上单次最多只能生成 <strong>10页</strong>。</p>
              <p>如果您选择继续：</p>
              <ul style="margin: 10px 0; padding-left: 20px;">
                <li>系统将只生成前 10 页内容</li>
                <li>超出部分将被自动截断</li>
                <li>建议您分批处理长文本</li>
              </ul>
              <p style="color: #666; font-size: 14px;">
                💡 提示：您可以将长文本分成多个部分，分别生成，或者自行搭建本项目来处理更长的文本
              </p>
              <p style="color: #888; font-size: 12px; margin-top: 10px;">
                注：此限制仅适用于 handwrite.14790897.xyz 网站
              </p>
            </div>
          `,
          icon: 'warning',
          showCancelButton: true,
          confirmButtonText: '继续生成（前10页）',
          cancelButtonText: '取消',
          confirmButtonColor: '#f39c12',
          cancelButtonColor: '#d33',
          width: '500px'
        });

        return result.isConfirmed;
      } catch (error) {
        console.error('SweetAlert2 error:', error);
        // 降级到原生 confirm
        return confirm(`检测到您的文本预计会生成 ${estimatedPages} 页。\n\n由于服务器资源限制，在 handwrite.14790897.xyz 网站上单次最多只能生成 10页。\n\n是否继续生成前10页？`);
      }
    },

    // 截断文本到指定页数
    truncateTextToPages(maxPages) {
      if (!this.text || this.text.length === 0) {
        return;
      }

      // 获取页面参数
      const pageWidth = this.width || (this.backgroundImage ?2481 : 2481); // 默认宽度
      const pageHeight = this.height || (this.backgroundImage ? 3507 : 3507); // 默认高度
      const fontSize = parseInt(this.fontSize) || 20;
      const lineSpacing = parseInt(this.lineSpacing) || 30;
      const marginTop = parseInt(this.marginTop) || 50;
      const marginBottom = parseInt(this.marginBottom) || 50;
      const marginLeft = parseInt(this.marginLeft) || 50;
      const marginRight = parseInt(this.marginRight) || 50;

      // 计算可用区域
      const usableWidth = pageWidth - marginLeft - marginRight;
      const usableHeight = pageHeight - marginTop - marginBottom;

      // 估算每行字符数
      const avgCharWidth = fontSize * 0.8;
      const charsPerLine = Math.floor(usableWidth / avgCharWidth);

      // 估算每页行数
      const linesPerPage = Math.floor(usableHeight / lineSpacing);

      // 计算每页字符数
      const charsPerPage = charsPerLine * linesPerPage;

      // 计算最大字符数
      const maxChars = charsPerPage * maxPages;

      // 截断文本
      if (this.text.length > maxChars) {
        const originalLength = this.text.length;
        this.text = this.text.substring(0, maxChars);

        console.log('文本截断:', {
          originalLength,
          truncatedLength: this.text.length,
          maxPages,
          charsPerPage,
          maxChars
        });

      }
    },

    // 启动冷却时间定时器
    startCooldownTimer() {
      // 清除现有定时器
      if (this.cooldownTimer) {
        clearInterval(this.cooldownTimer);
      }

      // 设置初始冷却状态
      this.isInCooldownPeriod = true;
      this.remainingCooldown = Math.ceil(this.generateCooldown / 1000);

      // 启动新定时器，每1秒更新一次显示
      this.cooldownTimer = setInterval(() => {
        const currentTime = Date.now();
        const timeSinceLastGenerate = currentTime - this.lastGenerateTime;
        const remaining = this.generateCooldown - timeSinceLastGenerate;

        if (remaining <= 0) {
          // 冷却结束
          this.isInCooldownPeriod = false;
          this.remainingCooldown = 0;
          clearInterval(this.cooldownTimer);
          this.cooldownTimer = null;
        } else {
          // 更新剩余时间
          this.remainingCooldown = Math.ceil(remaining / 1000);
        }
      }, 1000);
    },

  },

  mounted() {
    // 还原出来的栏宽是按当初那个窗口算的，进页面时先按当前窗口收一次
    this.clampWorkspaceColumns();
    window.addEventListener('resize', this.clampWorkspaceColumns);
  },

  // 组件销毁时清理定时器
  beforeUnmount() {
    window.removeEventListener('handwriting-text-loaded', this.onTextLoaded);
    window.removeEventListener('resize', this.clampWorkspaceColumns);

    if (this.cooldownTimer) {
      clearInterval(this.cooldownTimer);
      this.cooldownTimer = null;
    }
  },

};
</script>


<style scoped>
/* ===== 整体：顶部操作栏 + 三栏工作区 ===== */
#app-shell {
  display: flex;
  flex-direction: column;
  /* 固定为一屏高，工作区拿剩余空间，三栏在各自高度内滚动，整页不滚动。
     dvh 让带动态工具栏的移动浏览器（宽度 >1000px 的平板）也算得对可视高度，
     不支持的浏览器忽略这一行、回落到 100vh。 */
  height: 100vh;
  height: 100dvh;
}

/* 只有新版三栏需要左对齐；旧版沿用全局 #app 的居中对齐 */
#app-shell:not(.legacy-mode) {
  text-align: left;
}

.app-header {
  position: sticky;
  top: 0;
  z-index: 20;
  padding: 10px 20px;
  background: #fff;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}

.header-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
}

/* 操作按钮靠左排布：右上角要留给 SweetAlert 的 top-end toast，避免通知盖住按钮 */
.app-title {
  margin-right: 8px;
  font-size: 1.15rem;
  font-weight: 700;
  color: #2c3e50;
  white-space: nowrap;
}

.header-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.header-divider {
  width: 1px;
  height: 22px;
  margin: 0 2px;
  background: #dde1e6;
}

/* 操作按钮：顶栏与左栏共用 */
.action-btn {
  display: inline-block;
  padding: 8px 14px;
  border: 1px solid transparent;
  border-radius: 5px;
  font-size: 0.9rem;
  font-weight: bold;
  line-height: 1.2;
  text-decoration: none;
  cursor: pointer;
  transition: all 0.2s ease-in-out;
}

.action-btn.primary {
  color: #fff;
  background: #007BFF;
  border-color: #007BFF;
}

.action-btn.secondary {
  color: #007BFF;
  background: #fff;
  border-color: #007BFF;
}

.action-btn.info {
  color: #fff;
  background: #17a2b8;
  border-color: #17a2b8;
}

.action-btn.small {
  padding: 7px 10px;
  font-size: 0.85rem;
}

.action-btn:hover:not(:disabled) {
  transform: scale(1.05);
  box-shadow: 0 0 8px rgba(0, 0, 0, 0.25);
}

.action-btn.primary:hover:not(:disabled) {
  background: #0056b3;
  border-color: #0056b3;
}

.action-btn.secondary:hover:not(:disabled) {
  background: #e3f2fd;
}

.action-btn.info:hover {
  background: #138496;
  border-color: #138496;
}

.action-btn:active:not(:disabled) {
  transform: scale(0.96);
}

.action-btn.primary:active:not(:disabled) {
  background: #003d73;
  border-color: #003d73;
}

.action-btn:disabled {
  color: #fff;
  background: #ccc;
  border-color: #ccc;
  cursor: not-allowed;
}

/* 提示信息 */
#message {
  margin-top: 8px;
}

#message .alert {
  margin-bottom: 0;
  padding: 8px 12px;
  font-size: 0.9rem;
}

/* ===== 三栏工作区 ===== */
.workspace {
  flex: 1 1 auto;
  /* 允许在工作区内部收缩：顶栏变高（例如出现提示条）时让三栏变矮，而不是把整页撑出滚动条 */
  min-height: 0;
  display: grid;
  /* 5 条轨道 = 左栏 / 分隔条 / 中栏 / 分隔条 / 右栏。两条 16px 的轨道就是原来的 gap，
     由 .resizer 占满、兼作拖动热区，所以这里不再用 gap。
     左右两栏拖过之后是固定像素（--col-*），中栏吃掉剩余空间；没拖过就走 var() 的默认值。 */
  grid-template-columns:
    var(--col-left, 300px) 16px minmax(0, 1.2fr) 16px var(--col-right, minmax(0, 1fr));
  padding: 16px 20px;
}

/* 栏间分隔条：平时不显形，悬停/聚焦/拖动时才出现一条竖线 */
.resizer {
  position: relative;
  cursor: col-resize;
  /* 触控设备上把手势交给 pointer 事件，别让它变成滚动 */
  touch-action: none;
}

.resizer:focus {
  outline: none;
}

.resizer::before {
  content: "";
  position: absolute;
  top: 0;
  bottom: 0;
  left: 50%;
  width: 2px;
  margin-left: -1px;
  border-radius: 1px;
  background: transparent;
  transition: background 0.15s;
}

.resizer:hover::before {
  background: #9db3cf;
}

.resizer:focus-visible::before,
.resizer.active::before {
  background: #007BFF;
}

.panel {
  padding: 14px 16px;
  background: #fff;
  border: 1px solid #ddd;
  border-radius: 5px;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
  box-sizing: border-box;
  /* 高度由工作区剩余空间决定，内容超出时本栏自己滚动 */
  max-height: 100%;
  overflow-y: auto;
}

.panel-title {
  margin: 0 0 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #eef0f2;
  font-size: 1rem;
  font-weight: 700;
  color: #2c3e50;
  text-align: left;
}

/* ===== 左栏：参数设置 ===== */
.field-label {
  display: block;
  margin: 10px 0 6px;
  font-size: 0.9rem;
  font-weight: 600;
  color: #444;
  text-align: left;
}

.panel-settings .label-container {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.panel-settings .label-container label {
  flex: 1 1 auto;
  margin: 0;
  font-size: 0.9rem;
  white-space: nowrap;
  text-align: left;
}

.panel-settings input[type="number"],
.panel-settings input[type="text"] {
  flex: 0 0 110px;
  width: 110px;
  padding: 5px 8px;
  border: 1px solid #ddd;
  border-radius: 5px;
  box-sizing: border-box;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

/* 高级参数卡片：标签与输入框上下排列，宽度占满。
   限定在左栏里，否则同为 #collapseContent 的旧版分支会被一起改掉 */
.panel-settings #collapseContent .label-container {
  display: block;
}

.panel-settings #collapseContent .label-container label {
  display: block;
  white-space: normal;
}

.panel-settings #collapseContent .label-container input {
  width: 100%;
  margin-top: 4px;
}

.check-container {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 8px 0;
}

.check-container label {
  margin: 0;
  font-size: 0.9rem;
  text-align: left;
}

.advanced-toggle {
  width: 100%;
  margin: 10px 0;
  font-size: 0.9rem;
}

.font-selection {
  display: flex;
  align-items: center;
  gap: 8px;
}

.font-select {
  flex: 1 1 auto;
  min-width: 0;
}

.image-container {
  position: relative;
  margin-bottom: 6px;
}

.button-container {
  display: flex;
  align-items: center;
  gap: 8px;
  position: relative;
}

.panel-settings .preset-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #eef0f2;
}

.panel-settings .preset-row label {
  margin: 0;
  font-size: 0.9rem;
  white-space: nowrap;
}

.panel-settings .preset-row .styled-select {
  flex: 1 1 auto;
  min-width: 0;
}

/* ===== 中栏：正文 ===== */
.panel-text {
  display: flex;
  flex-direction: column;
}

/* 正文输入区撑满中栏剩余高度。
   用 id + 类提高优先级，覆盖 TextInput 自己的 #text_file_select 规则；
   旧版分支不挂 .text-input-fill，保持改造前那个 400px 居中窄栏。 */
#text_file_select.text-input-fill {
  flex: 1 1 auto;
  width: 100%;
  max-width: none;
  min-height: 320px;
  margin: 0;
}

#text_file_select.text-input-fill :deep(#textArea) {
  flex: 1 1 auto;
  min-height: 240px;
  font-size: 1rem;
  line-height: 1.8;
  resize: vertical;
}

/* 中栏标题已经说明这是正文栏，隐藏重复的字段标签；旧版仍显示「文字:」 */
#text_file_select.text-input-fill :deep(.text-field-label) {
  display: none;
}

.letter-format-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
  flex: 0 0 auto;
}

.letter-format-actions button {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin: 0;
  padding: 8px 12px;
  border-radius: 5px;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.3s ease-in-out;
}

.letter-format-button {
  color: white;
  background: #007BFF;
  border: 1px solid #007BFF;
  box-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
}

.letter-format-button:hover {
  background: #0056b3;
  border-color: #0056b3;
  transform: scale(1.05);
}

.letter-format-button:active {
  background: #003d73;
  border-color: #003d73;
  transform: scale(0.95);
}

.letter-format-undo {
  color: #2c3e50;
  background: white;
  border: 1px solid #ddd;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}

.letter-format-undo:hover {
  color: #0056b3;
  background: #e3f2fd;
  border-color: #007BFF;
}

.letter-format-mark {
  width: 18px;
  height: 18px;
  display: inline-grid;
  place-items: center;
  color: #007BFF;
  background: white;
  border-radius: 3px;
  font-size: 12px;
  font-weight: bold;
  line-height: 1;
}

/* ===== 右栏：预览 ===== */
.panel-preview {
  min-width: 100px;
}

.preview-nav {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.preview-page-indicator {
  font-size: 0.9rem;
  font-weight: bold;
}

.preview-image {
  max-width: 100%;
  height: auto;
  padding: 5px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

/* ===== 通用控件 ===== */
.styled-select {
  padding: 8px 10px;
  border: none;
  border-radius: 5px;
  color: white;
  background-color: #4285f4;
  font-size: 0.95rem;
  transition: all 0.3s ease-in-out;
}

.styled-select:hover {
  transform: scale(1.02);
  box-shadow: 0px 0px 8px rgba(0, 0, 0, 0.3);
}

.styled-select:focus {
  outline: none;
}

.styled-select:disabled {
  background-color: #b9c3cc;
  cursor: not-allowed;
}

input[type="number"],
input[type="text"],
input[type="file"] {
  transition: all 0.3s ease;
}

input[type="number"]:hover,
input[type="text"]:hover,
input[type="file"]:hover {
  box-shadow: 0px 0px 8px rgba(0, 0, 0, 0.2);
}

.close {
  border: none !important;
}

.button-disabled {
  background-color: #ccc !important;
  color: #666 !important;
  cursor: not-allowed !important;
}

.optionUnderline {
  margin: 0;
  padding: 0;
  width: 10px;
  padding: 0 !important;
  border-radius: 0 !important;
  border: none !important;
  box-shadow: none !important;
  box-sizing: content-box !important;
}

.optionEnglishSpacing {
  margin: 0;
  padding: 0;
  width: 10px;
  padding: 0 !important;
  border-radius: 0 !important;
  border: none !important;
  box-shadow: none !important;
  box-sizing: content-box !important;
}

.clear-button {
  position: relative;
  top: 5px;
  right: 5px;
  width: 12px;
  height: 12px;
  cursor: pointer;
}

.clear-button-line {
  position: absolute;
  left: 1px;
  width: 10px;
  height: 2px;
  background-color: #000;
}

.clear-button-line:first-child {
  top: 5px;
  transform: rotate(45deg);
}

.clear-button-line:last-child {
  top: 5px;
  transform: rotate(-45deg);
}

.loader {
  border: 16px solid #f3f3f3;
  /* Light grey */
  border-top: 16px solid #3498db;
  /* Blue */
  border-radius: 50%;
  width: 120px;
  height: 120px;
  animation: spin 2s linear infinite;
  position: absolute;
  /* 设置动画为绝对定位 */
  top: 50%;
  /* 将动画定位在父元素的中心 */
  left: 50%;
  transform: translate(-50%, -50%);
  /* 用 transform 属性将动画元素的中心对准父元素的中心 */
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }

  100% {
    transform: rotate(360deg);
  }
}

.freeprompt {
  font-size: 0.8rem;
  color: #e70808;
  text-align: center;
  margin-top: 10px;
}

.version-tag {
  margin-left: 8px;
  font-size: 0.8rem;
  color: #6c757d;
}

/* 生成状态提示样式 */
/* 队列已满提示 - 已迁移到 Swal Toast */
/* 生成状态/页数提示的样式已随组件移到 components/GenerationStatus.vue */

/* ===== 旧版布局：顶栏「旧版界面」按钮切回，样式沿用改造前那一套 ===== */
#app-shell.legacy-mode {
  /* 旧版是整页滚动，而不是三栏各自滚动 */
  height: auto;
  min-height: 100vh;
}

.legacy-root {
  display: grid;
  grid-template-areas: "form image";
  grid-template-columns: 1fr 2fr;
  flex: 1 1 auto;
  box-sizing: border-box;
  /* 改造前这层是 Bootstrap 的 .container（居中限宽）。换成 .legacy-root 后要自己补回来，
     否则宽屏下旧版整页铺满，还会和仍用 .container 的页脚对不齐 */
  width: 100%;
  max-width: 1320px;
  margin: 0 auto;
  padding: 0 12px;
}

.legacy-root #form {
  grid-area: form;
  max-width: 650px;
  column-count: auto;
  column-width: 200px;
  column-gap: 1em;
  width: 80vw;
  padding: 20px;
  margin: 0 auto;
  box-sizing: border-box;
  overflow: auto;
  box-shadow: 0 -1px 5px rgba(0, 0, 0, 0.1);
}

.legacy-root #form label {
  margin-bottom: 10px;
}

.legacy-root #form input,
.legacy-root #form textarea {
  width: 50%;
  padding: 10px;
  border-radius: 5px;
  border: 1px solid #ddd;
  box-sizing: border-box;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}

.legacy-root .label-container {
  display: flex;
  align-items: center;
}

.legacy-root .container_file {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-width: 400px;
  margin: auto;
}

.legacy-root .container_file label {
  font-size: 1.2rem;
  font-weight: 500;
}

/* 书信排版按钮有自己的一套配色，交给 .letter-format-* 规则 */
.legacy-root .container_file button:not(.letter-format-button):not(.letter-format-undo) {
  padding: 10px 5px;
  font-size: 0.9rem;
  color: white;
  background-color: #4285f4;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  margin: 0 auto;
}

.legacy-root .container_file button:disabled {
  background-color: grey;
}

.legacy-root .container_file span {
  margin-top: 5px;
  font-size: 0.9rem;
  color: #444;
}

.legacy-root .letter-format-actions {
  max-width: 400px;
  margin: 10px auto 0;
}

/* 旧版的内置预设行沿用改造前的居中样式（新版左栏那套带分隔线的写在 .panel-settings 下） */
.legacy-root .preset-row {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 8px;
  margin: 8px 0;
}

.legacy-root .preset-row label {
  margin: 0;
}

.legacy-root .preset-row .styled-select {
  min-width: 220px;
}

.legacy-root .preview {
  grid-area: image;
  padding: 20px;
  box-sizing: border-box;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
  min-width: 100px;
  min-height: 200px;
}

.legacy-root .preview img {
  max-width: 100%;
  height: auto;
  object-fit: cover;
  position: sticky;
  top: 0;
}

/* 窄屏：三栏堆叠成单栏，恢复整页滚动，不再限制每栏高度 */
@media (max-width: 1000px) {
  #app-shell {
    height: auto;
    min-height: 100vh;
  }

  /* 顶栏按钮在窄屏会换行到两三行，吸顶会长期占掉小屏近三分之一的高度 */
  .app-header {
    position: static;
  }

  .workspace {
    grid-template-columns: 1fr;
    /* 宽屏那两条 16px 间隔改由分隔条占据，堆叠时得把行间距补回来 */
    gap: 16px;
  }

  /* 单栏堆叠时没有「栏间距」可调，分隔条一并去掉（否则会多出两条 16px 的空行） */
  .resizer {
    display: none;
  }

  .panel {
    max-height: none;
  }

  .legacy-root {
    grid-template-areas:
      "form"
      "image";
    grid-template-columns: 1fr;
  }

  /* 单栏时收窄参数行，避免标签与输入框被拉得太远 */
  .panel-settings .label-container,
  .panel-settings .check-container,
  .panel-settings .font-selection,
  .panel-settings .image-container,
  .panel-settings .advanced-toggle,
  .panel-settings .preset-row {
    max-width: 420px;
  }
}
</style>
