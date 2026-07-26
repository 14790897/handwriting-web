<template>
  <div class="letter-overlay" @click.self="closeDialog">
    <section
      class="letter-dialog"
      role="dialog"
      aria-modal="true"
      :aria-labelledby="titleId"
    >
      <header class="letter-header">
        <div class="letter-heading">
          <span class="letter-seal" aria-hidden="true">信</span>
          <div>
            <h2 :id="titleId">{{ $t("message.letterFormatTitle") }}</h2>
            <p>{{ $t("message.letterFormatDescription") }}</p>
          </div>
        </div>
        <button
          type="button"
          class="letter-close"
          :aria-label="$t('message.cancel')"
          @click="closeDialog"
        >
          ×
        </button>
      </header>

      <div class="letter-content">
        <form class="letter-form" @submit.prevent="applyFormatting">
          <div class="letter-rule-summary">
            <span class="letter-rule-number">01</span>
            <span>{{ $t("message.letterRuleIndent") }}</span>
            <span class="letter-rule-number">02</span>
            <span>{{ $t("message.letterRuleSpacing") }}</span>
            <span class="letter-rule-number">03</span>
            <span>{{ $t("message.letterRuleEnding") }}</span>
          </div>

          <div v-if="detectedEnding" class="letter-detected">
            <span>{{ $t("message.letterEndingDetected") }}</span>
            <button type="button" @click="restoreEndingToBody">
              {{ $t("message.letterRestoreEnding") }}
            </button>
          </div>

          <label class="letter-field">
            <span>{{ $t("message.letterSignature") }}</span>
            <textarea
              ref="signatureInput"
              v-model.trim="signature"
              autocomplete="name"
              :placeholder="$t('message.letterSignaturePlaceholder')"
              rows="2"
            ></textarea>
            <small>{{ $t("message.letterSignatureHelp") }}</small>
          </label>

          <label class="letter-field">
            <span>{{ $t("message.letterDate") }}</span>
            <input
              v-model.trim="date"
              type="text"
              :placeholder="$t('message.letterDatePlaceholder')"
            />
          </label>
        </form>

        <aside class="letter-preview">
          <div class="letter-preview-heading">
            <span>{{ $t("message.letterPreview") }}</span>
            <span>{{ $t("message.letterPreviewHint") }}</span>
          </div>
          <div class="letter-paper">
            <div
              v-for="(line, index) in previewLines"
              :key="`${index}-${line.text}`"
              class="letter-paper-line"
              :class="{
                'is-right': line.isRight,
                'is-ellipsis': line.isEllipsis,
              }"
            >
              {{ line.text }}
            </div>
          </div>
        </aside>
      </div>

      <footer class="letter-footer">
        <button type="button" class="letter-button is-secondary" @click="closeDialog">
          {{ $t("message.cancel") }}
        </button>
        <button
          type="button"
          class="letter-button is-primary"
          :disabled="!canApply"
          @click="applyFormatting"
        >
          {{ $t("message.letterApply") }}
        </button>
      </footer>
    </section>
  </div>
</template>

<script>
import {
  extractLetterEnding,
  formatChineseLetter,
  restoreLetterEnding,
} from "../utils/chineseLetterFormatter.mjs";

export default {
  name: "ChineseLetterFormatter",
  props: {
    sourceText: {
      type: String,
      required: true,
    },
  },
  emits: ["apply", "close"],
  data() {
    return {
      titleId: `letter-format-title-${Math.random().toString(36).slice(2)}`,
      bodyText: "",
      signature: "",
      date: "",
      detectedEnding: false,
      returnFocusElement: null,
    };
  },
  computed: {
    formattedText() {
      return formatChineseLetter({
        body: this.bodyText,
        signature: this.signature,
        date: this.date,
      });
    },
    canApply() {
      return Boolean(this.bodyText.trim());
    },
    previewLines() {
      const lines = this.formattedText.split("\n").filter(Boolean);
      const visibleLines =
        lines.length > 12
          ? [...lines.slice(0, 8), "…", ...lines.slice(-2)]
          : lines;

      return visibleLines.map((line) => ({
        text: line.replace(/^>>>[ \t]?/, ""),
        isRight: line.startsWith(">>>"),
        isEllipsis: line === "…",
      }));
    },
  },
  created() {
    const ending = extractLetterEnding(this.sourceText);
    this.bodyText = ending.body;
    this.signature = ending.signature;
    this.date = ending.date;
    this.detectedEnding = ending.detectedEnding;
  },
  mounted() {
    this.returnFocusElement = document.activeElement;
    document.addEventListener("keydown", this.handleKeydown);
    this.$nextTick(() => this.$refs.signatureInput?.focus());
  },
  beforeUnmount() {
    document.removeEventListener("keydown", this.handleKeydown);
    this.returnFocusElement?.focus();
  },
  methods: {
    handleKeydown(event) {
      if (event.key === "Escape") {
        this.closeDialog();
        return;
      }
      if (event.key !== "Tab") return;

      const focusableElements = Array.from(
        this.$el.querySelectorAll(
          'button:not(:disabled), input:not(:disabled), textarea:not(:disabled), [tabindex]:not([tabindex="-1"])'
        )
      );
      if (focusableElements.length === 0) return;

      const firstElement = focusableElements[0];
      const lastElement = focusableElements[focusableElements.length - 1];
      if (event.shiftKey && document.activeElement === firstElement) {
        event.preventDefault();
        lastElement.focus();
      } else if (!event.shiftKey && document.activeElement === lastElement) {
        event.preventDefault();
        firstElement.focus();
      }
    },
    closeDialog() {
      this.$emit("close");
    },
    restoreEndingToBody() {
      this.bodyText = restoreLetterEnding({
        body: this.bodyText,
        signature: this.signature,
        date: this.date,
      });
      this.signature = "";
      this.date = "";
      this.detectedEnding = false;
    },
    applyFormatting() {
      if (!this.canApply) return;
      this.$emit("apply", this.formattedText);
    },
  },
};
</script>

<style scoped>
.letter-overlay {
  position: fixed;
  inset: 0;
  z-index: 2147483640;
  display: grid;
  place-items: center;
  padding: 24px;
  background: rgba(31, 35, 40, 0.58);
  backdrop-filter: blur(3px);
}

.letter-dialog {
  width: min(840px, 100%);
  max-height: calc(100vh - 48px);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  color: #2d2925;
  background: #f9f5ec;
  border: 1px solid rgba(111, 85, 62, 0.25);
  border-radius: 12px;
  box-shadow: 0 24px 70px rgba(24, 20, 17, 0.3);
  text-align: left;
}

.letter-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  padding: 22px 24px 18px;
  border-bottom: 1px solid rgba(111, 85, 62, 0.18);
}

.letter-heading {
  display: flex;
  align-items: center;
  gap: 14px;
}

.letter-heading h2 {
  margin: 0 0 4px;
  font-family: "Songti SC", "STSong", serif;
  font-size: 21px;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.letter-heading p {
  margin: 0;
  color: #71675e;
  font-size: 13px;
}

.letter-seal {
  flex: 0 0 38px;
  height: 38px;
  display: grid;
  place-items: center;
  color: #fff9ec;
  background: #963b32;
  border-radius: 4px;
  font-family: "Songti SC", "STSong", serif;
  font-size: 21px;
  box-shadow: inset 0 0 0 2px rgba(255, 249, 236, 0.22);
}

.letter-close {
  width: 32px;
  height: 32px;
  padding: 0;
  border: 0;
  border-radius: 50%;
  color: #776b61;
  background: transparent;
  font-size: 22px;
  line-height: 1;
  cursor: pointer;
}

.letter-close:hover {
  color: #963b32;
  background: rgba(150, 59, 50, 0.08);
}

.letter-content {
  min-height: 0;
  overflow-y: auto;
  display: grid;
  grid-template-columns: minmax(260px, 0.85fr) minmax(320px, 1.15fr);
  gap: 24px;
  padding: 24px;
}

.letter-form {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.letter-rule-summary {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 9px 10px;
  padding-bottom: 18px;
  border-bottom: 1px solid rgba(111, 85, 62, 0.18);
  color: #514942;
  font-size: 13px;
}

.letter-rule-number {
  color: #963b32;
  font-family: Georgia, serif;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.letter-detected {
  margin: -4px 0 0;
  padding: 9px 11px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  color: #31593b;
  background: #edf5ec;
  border: 1px solid #c6ddc5;
  border-radius: 6px;
  font-size: 12px;
}

.letter-detected button {
  flex: 0 0 auto;
  padding: 3px 7px;
  color: #31593b;
  background: transparent;
  border: 1px solid #8eb28e;
  border-radius: 4px;
  font-size: 11px;
  cursor: pointer;
}

.letter-detected button:hover {
  background: #dcebdc;
}

.letter-field {
  display: flex;
  flex-direction: column;
  gap: 7px;
}

.letter-field > span {
  color: #39332e;
  font-size: 13px;
  font-weight: 650;
}

.letter-field input,
.letter-field textarea {
  width: 100%;
  padding: 8px 11px;
  color: #2d2925;
  background: rgba(255, 253, 247, 0.9);
  border: 1px solid #c9bcad;
  border-radius: 6px;
  outline: none;
  font-size: 14px;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.letter-field input {
  height: 38px;
}

.letter-field textarea {
  min-height: 64px;
  resize: vertical;
  line-height: 1.5;
}

.letter-field input:focus,
.letter-field textarea:focus {
  border-color: #963b32;
  box-shadow: 0 0 0 3px rgba(150, 59, 50, 0.12);
}

.letter-field small {
  color: #81766c;
  font-size: 11px;
  line-height: 1.5;
}

.letter-preview {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 9px;
}

.letter-preview-heading {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  color: #39332e;
  font-size: 13px;
  font-weight: 650;
}

.letter-preview-heading span:last-child {
  color: #8a7f74;
  font-size: 11px;
  font-weight: 400;
}

.letter-paper {
  flex: 1 1 auto;
  min-height: 290px;
  padding: 28px 30px;
  overflow: hidden;
  color: #292521;
  background-color: #fffdf7;
  background-image: linear-gradient(
    to bottom,
    transparent 31px,
    rgba(126, 99, 73, 0.08) 32px
  );
  background-size: 100% 32px;
  border: 1px solid #d8cbb9;
  box-shadow: 0 10px 26px rgba(76, 57, 40, 0.1);
  font-family: "Songti SC", "STSong", serif;
  font-size: 15px;
  line-height: 32px;
}

.letter-paper-line {
  min-height: 32px;
  white-space: pre-wrap;
  word-break: break-all;
}

.letter-paper-line.is-right {
  text-align: right;
}

.letter-paper-line.is-ellipsis {
  color: #9a8f84;
  text-align: center;
  letter-spacing: 0.3em;
}

.letter-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 14px 24px;
  background: rgba(238, 230, 217, 0.65);
  border-top: 1px solid rgba(111, 85, 62, 0.18);
}

.letter-button {
  height: 36px;
  padding: 0 17px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 650;
  cursor: pointer;
}

.letter-button.is-secondary {
  color: #554c44;
  background: transparent;
  border: 1px solid #bfb2a4;
}

.letter-button.is-primary {
  color: #fffaf0;
  background: #963b32;
  border: 1px solid #963b32;
}

.letter-button.is-primary:hover:not(:disabled) {
  background: #7f3029;
}

.letter-button:disabled {
  opacity: 0.42;
  cursor: not-allowed;
}

@media (max-width: 720px) {
  .letter-overlay {
    align-items: end;
    padding: 0;
  }

  .letter-dialog {
    max-height: 94vh;
    max-height: 94dvh;
    border-radius: 14px 14px 0 0;
  }

  .letter-header,
  .letter-content,
  .letter-footer {
    padding-left: 18px;
    padding-right: 18px;
  }

  .letter-content {
    grid-template-columns: 1fr;
  }

  .letter-paper {
    min-height: 230px;
  }

  .letter-footer {
    padding-bottom: calc(14px + env(safe-area-inset-bottom, 0px));
  }
}
</style>
