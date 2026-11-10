import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { finalize } from 'rxjs';

@Component({
  imports: [ReactiveFormsModule],
  selector: 'app-root',
  styleUrl: './app.css',
  templateUrl: './app.html',
})
export class App {
  private readonly http = inject(HttpClient);
  private readonly fb = inject(FormBuilder);

  protected readonly form = this.fb.nonNullable.group({
    name: ['', [Validators.required, Validators.maxLength(255)]],
    email: ['', [Validators.required, Validators.email]],
  });

  protected readonly submitting = signal(false);
  protected readonly success = signal<string | null>(null);
  protected readonly error = signal<string | null>(null);

  protected submit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    this.submitting.set(true);
    this.success.set(null);
    this.error.set(null);

    const { name, email } = this.form.getRawValue();
    this.http
      .post<{ email: string }>('/api/subscribers', { name: name.trim(), email })
      .pipe(finalize(() => this.submitting.set(false)))
      .subscribe({
        next: (body) => {
          this.success.set(
            `Confirmation sent to ${body.email}. Check your inbox.`,
          );
          this.form.reset();
        },
        error: (err: HttpErrorResponse) => {
          this.error.set(
            typeof err.error?.detail === 'string'
              ? err.error.detail
              : 'Something went wrong. Please try again.',
          );
        },
      });
  }
}
