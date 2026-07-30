import * as React from "react";
import { Eye, EyeOff, type LucideIcon } from "lucide-react";

import { cn } from "@/lib/utils";

type ProprietesInput = React.ComponentProps<"input"> & {
  /** Icône affichée à l'intérieur du champ, à gauche. Purement décorative. */
  icone?: LucideIcon;
};

const CLASSES_BASE =
  "flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-base shadow-sm transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-foreground placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50 md:text-sm";

const Input = React.forwardRef<HTMLInputElement, ProprietesInput>(
  ({ className, type, icone: Icone, disabled, ...props }, ref) => {
    const [visible, setVisible] = React.useState(false);

    // Un champ mot de passe se révèle : sur mobile, saisir à l'aveugle est la
    // première cause d'échec de connexion.
    const estMotDePasse = type === "password";
    const typeEffectif = estMotDePasse && visible ? "text" : type;

    const champ = (
      <input
        type={typeEffectif}
        disabled={disabled}
        className={cn(CLASSES_BASE, Icone && "pl-9", estMotDePasse && "pr-9", className)}
        ref={ref}
        {...props}
      />
    );

    if (!Icone && !estMotDePasse) return champ;

    return (
      <div className="relative">
        {Icone ? (
          <Icone
            aria-hidden="true"
            className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"
          />
        ) : null}
        {champ}
        {estMotDePasse ? (
          <button
            type="button"
            disabled={disabled}
            onClick={() => setVisible((v) => !v)}
            aria-label={visible ? "Masquer le mot de passe" : "Afficher le mot de passe"}
            aria-pressed={visible}
            className="absolute right-0 top-0 flex h-full w-9 items-center justify-center rounded-r-md text-muted-foreground transition-colors hover:text-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
          >
            {visible ? (
              <EyeOff aria-hidden="true" className="h-4 w-4" />
            ) : (
              <Eye aria-hidden="true" className="h-4 w-4" />
            )}
          </button>
        ) : null}
      </div>
    );
  },
);
Input.displayName = "Input";

export { Input };
