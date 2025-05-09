# expert_logic.py
# REMINDER: Update requirements.txt if needed

import os
import io
import base64
import csv
from datetime import datetime
import time # Import time for potential delays/retries

import PyPDF2
import docx
# import openpyxl # Uncomment this line ONLY if you keep/uncomment the XLSX reading code below
from PIL import Image
from anthropic import Anthropic, APIError # Importer APIError pour une meilleure gestion des erreurs

# Constants
SEPARATOR_DOUBLE = "=" * 50
SEPARATOR_SINGLE = "-" * 50

# --- ExpertProfileManager Class ---
class ExpertProfileManager:
    def __init__(self, profile_dir="profiles"):
        self.profiles = {}
        self.profile_dir = profile_dir
        self.load_profiles()

    def load_profiles(self):
        """Charge les profils experts depuis le dossier spécifié."""
        print(f"Chargement des profils depuis: {self.profile_dir}")
        if not os.path.exists(self.profile_dir):
            print(f"AVERTISSEMENT: Le dossier de profils '{self.profile_dir}' n'existe pas.")
            if not self.profiles:
                 self.add_profile("default_expert", "Expert par Défaut", "Je suis un expert IA généraliste.")
            return

        try:
            profile_files = [f for f in os.listdir(self.profile_dir) if f.endswith('.txt')]
            if not profile_files:
                 print("Aucun fichier de profil .txt trouvé.")
                 if not self.profiles:
                     self.add_profile("default_expert", "Expert par Défaut", "Je suis un expert IA généraliste.")
                 return

            for profile_file in profile_files:
                profile_id = os.path.splitext(profile_file)[0]
                profile_path = os.path.join(self.profile_dir, profile_file)
                try:
                    with open(profile_path, 'r', encoding='utf-8') as file:
                        content = file.read().strip()
                        if not content:
                            print(f"AVERTISSEMENT: Fichier de profil vide: {profile_file}")
                            continue
                        lines = content.split('\n', 1)
                        name = lines[0].strip() if lines else f"Profil_{profile_id}"
                        profile_content = lines[1].strip() if len(lines) > 1 else f"Profil: {name}"
                        self.add_profile(profile_id, name, profile_content)
                        print(f"Profil chargé: {profile_id} - {name}")
                except Exception as e:
                    print(f"Erreur lors du chargement du profil {profile_file}: {str(e)}")

        except Exception as e:
            print(f"Erreur lors de l'accès au dossier des profils '{self.profile_dir}': {str(e)}")
            if not self.profiles:
                 self.add_profile("default_expert", "Expert par Défaut", "Je suis un expert IA généraliste.")


    def add_profile(self, profile_id, display_name, profile_content):
        self.profiles[profile_id] = {
            "id": profile_id,
            "name": display_name,
            "content": profile_content
        }

    def get_profile(self, profile_id):
        return self.profiles.get(profile_id, None)

    def get_profile_by_name(self, name):
        for profile in self.profiles.values():
            if profile["name"] == name:
                return profile
        return None

    def get_all_profiles(self):
        return self.profiles

    def get_profile_names(self):
        if not self.profiles:
            self.load_profiles()
        return [p["name"] for p in self.profiles.values()]


# --- ExpertAdvisor Class ---
class ExpertAdvisor:
    def __init__(self, api_key):
        if not api_key:
            raise ValueError("Clé API Anthropic manquante.")
        self.anthropic = Anthropic(api_key=api_key)
        print("Client API Anthropic initialisé.")
        self.model_name_global = "claude-3-7-sonnet-20250219" # Votre modèle unique
        print(f"Utilisation globale du modèle : {self.model_name_global}")

        self.supported_formats = ['.pdf', '.docx', '.xlsx', '.csv', '.txt',
                                  '.jpg', '.jpeg', '.png', '.webp']
        self.profile_manager = ExpertProfileManager()
        all_profiles = self.profile_manager.get_all_profiles()
        self.current_profile_id = list(all_profiles.keys())[0] if all_profiles else "default_expert"
        if not all_profiles:
             if not self.profile_manager.get_profile("default_expert"):
                 self.profile_manager.add_profile("default_expert", "Expert par Défaut", "Je suis un expert IA généraliste.")
             self.current_profile_id = "default_expert"

    def set_current_profile_by_name(self, profile_name):
        profile = self.profile_manager.get_profile_by_name(profile_name)
        if profile:
            self.current_profile_id = profile["id"]
            print(f"Profil expert changé en: {profile_name}")
            return True
        print(f"Erreur: Profil '{profile_name}' non trouvé.")
        return False

    def get_current_profile(self):
        profile = self.profile_manager.get_profile(self.current_profile_id)
        if not profile:
             available_profiles = self.profile_manager.get_all_profiles()
             if available_profiles:
                 first_profile_id = next(iter(available_profiles))
                 self.current_profile_id = first_profile_id
                 print(f"Avertissement: Profil ID {self.current_profile_id} invalide, retour au premier profil disponible: {first_profile_id}")
                 return available_profiles[first_profile_id]
             else:
                 print("Avertissement: Aucun profil chargé, utilisation d'un profil interne par défaut.")
                 return {"id": "default", "name": "Expert (Défaut)", "content": "Expert IA"}
        return profile

    def get_supported_filetypes_flat(self):
        return [ext.lstrip('.') for ext in self.supported_formats]

    def read_file(self, uploaded_file):
        file_ext = os.path.splitext(uploaded_file.name)[1].lower()
        if file_ext not in self.supported_formats:
            return f"Format de fichier non supporté: {uploaded_file.name}. Formats acceptés: {', '.join(self.supported_formats)}"
        try:
            file_bytes = uploaded_file.getvalue()
            file_stream = io.BytesIO(file_bytes)
            if file_ext == '.pdf': return self._read_pdf(file_stream, uploaded_file.name)
            elif file_ext == '.docx': return self._read_docx(file_stream, uploaded_file.name)
            elif file_ext in ['.xlsx', '.csv']: return self._read_spreadsheet(file_stream, uploaded_file.name, file_ext)
            elif file_ext == '.txt': return self._read_txt(file_stream, uploaded_file.name)
            elif file_ext in ['.jpg', '.jpeg', '.png', '.webp']: return self._read_image(file_bytes, uploaded_file.name, file_ext)
            else: return f"Format de fichier interne non géré : {uploaded_file.name}"
        except Exception as e: return f"Erreur générale lors de la lecture du fichier {uploaded_file.name}: {str(e)}"

    def _read_pdf(self, file_stream, filename):
        text = ""
        try:
            file_stream.seek(0)
            pdf_reader = PyPDF2.PdfReader(file_stream)
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text: text += page_text + "\n"
            if not text: return f"Aucun texte n'a pu être extrait de {filename}. Le PDF est-il basé sur une image ou protégé ?"
            return text
        except Exception as e: return f"Erreur lors de la lecture du PDF {filename}: {str(e)}"

    def _read_docx(self, file_stream, filename):
        try:
            file_stream.seek(0)
            doc = docx.Document(file_stream)
            return "\n".join([p.text for p in doc.paragraphs if p.text is not None])
        except Exception as e: return f"Erreur lors de la lecture du DOCX {filename}: {str(e)}"

    def _read_spreadsheet(self, file_stream, filename, file_ext):
        try:
            if file_ext == '.csv':
                file_stream.seek(0)
                decoded_content = None
                try: decoded_content = file_stream.read().decode('utf-8')
                except UnicodeDecodeError:
                    print(f"Décodage UTF-8 échoué pour {filename}, essai avec Latin-1.")
                    file_stream.seek(0)
                    try: decoded_content = file_stream.read().decode('latin1')
                    except Exception as de: return f"Erreur de décodage pour {filename}: {str(de)}"
                if decoded_content is None: return f"Impossible de décoder le contenu de {filename}."
                text_stream = io.StringIO(decoded_content)
                reader = csv.reader(text_stream)
                output_string_io = io.StringIO()
                writer = csv.writer(output_string_io, delimiter=',', quoting=csv.QUOTE_MINIMAL)
                for row in reader: writer.writerow(row)
                return output_string_io.getvalue()
            elif file_ext == '.xlsx':
                # Code pour lire XLSX avec openpyxl (si décommenté et bibliothèque installée)
                # try:
                #     import openpyxl
                #     file_stream.seek(0)
                #     workbook = openpyxl.load_workbook(file_stream)
                #     sheet = workbook.active
                #     csv_output = io.StringIO()
                #     writer = csv.writer(csv_output)
                #     for row in sheet.iter_rows(values_only=True):
                #         writer.writerow([str(cell) if cell is not None else "" for cell in row])
                #     return csv_output.getvalue()
                # except ImportError:
                #     return "INFO: La bibliothèque 'openpyxl' est requise pour lire les fichiers .xlsx. Veuillez l'installer."
                # except Exception as e_xlsx:
                #     return f"Erreur lors de la lecture du XLSX {filename}: {str(e_xlsx)}"
                return f"INFO: Le format XLSX nécessite 'openpyxl'. Pour l'activer, décommentez le code et ajoutez à requirements.txt."
        except Exception as e: return f"Erreur lors du traitement du tableur {filename}: {str(e)}"

    def _read_txt(self, file_stream, filename):
        try:
            file_stream.seek(0)
            try: return file_stream.read().decode('utf-8')
            except UnicodeDecodeError:
                print(f"Décodage UTF-8 échoué pour {filename}, essai avec Latin-1.")
                file_stream.seek(0)
                try: return file_stream.read().decode('latin1')
                except UnicodeDecodeError:
                    print(f"Décodage Latin-1 échoué pour {filename}, essai avec cp1252.")
                    file_stream.seek(0)
                    return file_stream.read().decode('cp1252', errors='replace')
        except Exception as e: return f"Erreur lors de la lecture du TXT {filename}: {str(e)}"

    def _read_image(self, file_bytes, filename, file_ext):
        try:
            img = Image.open(io.BytesIO(file_bytes))
            mime_types = {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.webp': 'image/webp'}
            mime_type = mime_types.get(file_ext)
            if not mime_type: return f"Format d'image non supporté par l'API: {filename}"
            
            # Claude 3 image size limits: max 5MB per image, max 20MB per request, max 1568x1568 pixels
            # Check size in bytes (approximate, as PIL re-encoding can change size)
            if len(file_bytes) > 5 * 1024 * 1024: # 5MB
                return f"L'image {filename} dépasse la limite de 5MB par image."

            max_pixels = 1568 * 1568 
            if img.width * img.height > max_pixels:
                 print(f"Redimensionnement de l'image {filename} car elle dépasse la taille max de pixels ({img.width}x{img.height}).")
                 img.thumbnail((1568, 1568), Image.Resampling.LANCZOS)

            buffered = io.BytesIO()
            img_format = mime_type.split('/')[1].upper()
            if img_format == 'JPEG' and img.mode in ('RGBA', 'LA', 'P'):
                 print(f"Conversion de l'image {filename} en RGB pour sauvegarde JPEG.")
                 img = img.convert('RGB')
            
            # Save with quality settings if JPEG to control size a bit more
            if img_format == 'JPEG':
                img.save(buffered, format=img_format, quality=85, optimize=True)
            else:
                img.save(buffered, format=img_format)

            # Final check on encoded size
            if buffered.tell() > 5 * 1024 * 1024:
                 return f"L'image {filename} après encodage/redimensionnement dépasse toujours 5MB."

            img_str = base64.b64encode(buffered.getvalue()).decode()
            return {'type': 'image', 'source': {'type': 'base64', 'media_type': mime_type, 'data': img_str}}
        except Exception as e: return f"Erreur lors du traitement de l'image {filename}: {str(e)}"

    def analyze_documents(self, uploaded_files, conversation_history):
        if not uploaded_files: return "Veuillez téléverser au moins un fichier.", []
        
        analysis_results, processed_contents, filenames, content_types = [], [], [], []
        total_image_size_mb = 0

        for uploaded_file in uploaded_files:
            content = self.read_file(uploaded_file)
            if isinstance(content, str) and (content.startswith("Erreur") or content.startswith("Format") or content.startswith("Aucun texte") or content.startswith("INFO") or content.startswith("Impossible") or content.startswith("L'image")):
                analysis_results.append((uploaded_file.name, content)) # Include error messages
            elif isinstance(content, dict) and content.get('type') == 'image':
                # Estimate size of base64 string for total request limit
                # Base64 is approx 4/3 original size. Add some overhead.
                image_size_bytes = len(content['source']['data']) * 3 / 4
                total_image_size_mb += image_size_bytes / (1024 * 1024)
                if total_image_size_mb > 18: # Leave some room for text and overhead from 20MB limit
                    analysis_results.append((uploaded_file.name, "Taille totale des images pour cette requête dépasserait la limite de l'API. Cette image n'a pas été ajoutée."))
                    continue # Skip this image
                processed_contents.append(content)
                filenames.append(uploaded_file.name)
                content_types.append('image')
            elif isinstance(content, str):
                 processed_contents.append(content)
                 filenames.append(uploaded_file.name)
                 content_types.append('text')
            else: 
                analysis_results.append((uploaded_file.name, f"Erreur interne: Type de contenu inattendu ({type(content)})"))

        if not processed_contents: 
            # If only errors, return them
            error_summary = "Aucun fichier n'a pu être traité avec succès pour l'analyse.\n"
            for name, reason in analysis_results:
                error_summary += f"- {name}: {reason}\n"
            return error_summary, analysis_results


        profile = self.get_current_profile()
        prompt_text_parts = [f"En tant qu'expert {profile['name']}, analysez le(s) contenu(s) suivant(s) provenant du/des fichier(s) nommé(s) : {', '.join(filenames)}."]
        history_str = self._format_history_for_api(conversation_history)
        if history_str != "Aucun historique": 
            prompt_text_parts.append(f"\nVoici l'historique récent de la conversation pour contexte:\n{SEPARATOR_SINGLE}\n{history_str}\n{SEPARATOR_SINGLE}")

        num_valid_files = len(processed_contents)
        
        if num_valid_files == 1:
            prompt_text_parts.append("\nAnalysez ce document/image et fournissez une analyse structurée comprenant :\n1.  **RÉSUMÉ / DESCRIPTION GÉNÉRALE:** Décrivez brièvement le contenu du fichier.\n2.  **ANALYSE TECHNIQUE / ÉLÉMENTS CLÉS:** Identifiez les points techniques, données, ou éléments visuels importants. S'il s'agit de plans ou schémas, décrivez-les.\n3.  **ANALYSE FINANCIÈRE (si applicable et possible):** Si des informations financières sont présentes ou peuvent être inférées, commentez-les.\n4.  **RECOMMANDATIONS / QUESTIONS:** Basé sur l'analyse, quelles sont vos recommandations ou quelles questions supplémentaires se posent ?")
        else:
            prompt_text_parts.append(f"\nAnalysez l'ensemble de ces documents/images et fournissez une synthèse intégrée :\n1.  **ANALYSE INDIVIDUELLE SUCCINCTE:** Pour chaque fichier ({', '.join(filenames)}), résumez son contenu principal et son type.\n2.  **POINTS COMMUNS ET DIVERGENCES:** Y a-t-il des thèmes, des données ou des informations qui se recoupent ou se contredisent entre les fichiers ?\n3.  **ANALYSE D'ENSEMBLE / SYNTHÈSE:** Quelle est la compréhension globale qui émerge de la combinaison de ces fichiers ?\n4.  **RECOMMANDATIONS INTÉGRÉES:** Quelles recommandations ou conclusions pouvez-vous tirer de l'ensemble des informations fournies ?")


        final_prompt_instruction = "\n".join(prompt_text_parts) + "\n\nFournissez votre réponse de manière claire et bien structurée."
        api_system_prompt = profile.get('content', 'Vous êtes un expert IA compétent.')
        
        user_message_content = []
        # Add images first as per Claude's best practices
        for i, content in enumerate(processed_contents):
            if content_types[i] == 'image': 
                user_message_content.append(content)
        
        # Then add text parts
        for i, content in enumerate(processed_contents):
             if content_types[i] == 'text':
                 user_message_content.append({"type": "text", "text": f"\n{SEPARATOR_DOUBLE}\nDEBUT Contenu Fichier: {filenames[i]}\n{SEPARATOR_SINGLE}\n{content}\n{SEPARATOR_SINGLE}\nFIN Contenu Fichier: {filenames[i]}\n{SEPARATOR_DOUBLE}\n"})
        
        # Add the final instruction
        user_message_content.append({"type": "text", "text": final_prompt_instruction})
        
        api_messages = [{"role": "user", "content": user_message_content}]

        try:
            print(f"Appel API Claude pour analyse de {num_valid_files} fichier(s)... Modèle: {self.model_name_global}")
            response = self.anthropic.messages.create(
                model=self.model_name_global, max_tokens=4000,
                messages=api_messages, system=api_system_prompt
            )
            if response.content and len(response.content) > 0 and response.content[0].text:
                api_response_text = response.content[0].text
                # Add successful analysis to results
                if num_valid_files > 0:
                    analysis_results.append(("Analyse Combinée" if num_valid_files > 1 else f"Analyse: {filenames[0]}", "Succès"))
                print("Analyse Claude terminée.")
                return api_response_text, analysis_results
            else:
                 error_msg = "Erreur: Réponse vide ou mal formée de l'API (analyse)."
                 print(error_msg)
                 if num_valid_files > 0:
                     analysis_results.append(("Erreur API Claude (Analyse)", error_msg))
                 return error_msg, analysis_results
        except APIError as e:
            error_msg = f"Erreur API Anthropic (analyse): {type(e).__name__} ({e.status_code}) - {e.message}"
            print(error_msg)
            if num_valid_files > 0:
                analysis_results.append(("Erreur API Claude (Analyse)", error_msg))
            return error_msg, analysis_results
        except Exception as e:
            error_msg = f"Erreur générique API (analyse): {type(e).__name__} - {str(e)}"
            print(error_msg)
            if num_valid_files > 0:
                analysis_results.append(("Erreur API Claude (Analyse)", error_msg))
            return error_msg, analysis_results

    def _format_history_for_api(self, conversation_history):
         if not conversation_history: return "Aucun historique"
         formatted_history = []
         turns_to_include = 5 # Number of user/assistant turn pairs
         
         # Iterate backwards to get the most recent turns
         user_turns = 0
         assistant_turns = 0
         temp_history = []
         for msg in reversed(conversation_history):
             if len(temp_history) >= turns_to_include * 2 : # Approx limit
                 break
             role, content = msg["role"], msg["content"]
             if role == "system": continue
             
             role_name = "Utilisateur" if role == "user" else "Expert"
             if role == "search_result": 
                 role_name = "InfoWeb"
                 content = f"[Résultat Recherche Web]: {content}"
             
             # Basic check for relevance, ignore very short/placeholder messages if needed
             # if len(str(content).strip()) < 10 and role != "user": continue 

             temp_history.append(f"{role_name}: {content}")

             if role == "user": user_turns +=1
             if role == "assistant": assistant_turns +=1
             if user_turns >= turns_to_include and assistant_turns >= turns_to_include:
                 break
        
         formatted_history = list(reversed(temp_history)) # Put back in chronological order
         return "\n".join(formatted_history) if formatted_history else "Aucun historique pertinent."


    def obtenir_reponse(self, question, conversation_history):
        profile = self.get_current_profile()
        if not profile: return "Erreur Critique: Profil expert non défini."
        
        api_messages_history = []
        # History for Claude API should be a list of {"role": "user/assistant", "content": ...}
        # Include a limited number of recent messages
        history_limit_pairs = 8 # Max user/assistant pairs
        
        # Filter and format history
        relevant_history = []
        for msg in conversation_history:
            role, content = msg.get("role"), msg.get("content")
            if role == "system" or not isinstance(content, str): # Skip system messages and non-string content for this
                continue
            
            # Map roles correctly for Claude
            api_role = None
            if role == "user":
                api_role = "user"
            elif role == "assistant" or role == "search_result":
                api_role = "assistant"
                if role == "search_result":
                    content = f"[Info from Web Search]:\n{content}"
            
            if api_role:
                relevant_history.append({"role": api_role, "content": content})
        
        # Take last N messages, ensuring it starts with user if possible, or just truncates
        start_index = max(0, len(relevant_history) - (history_limit_pairs * 2))
        api_messages_history = relevant_history[start_index:]

        api_messages_history.append({"role": "user", "content": question})
        
        api_system_prompt = profile.get('content', 'Vous êtes un expert IA utile.')
        
        try:
            print(f"Appel API Claude pour réponse conversationnelle... Modèle: {self.model_name_global}")
            response = self.anthropic.messages.create(
                model=self.model_name_global, 
                max_tokens=4000,
                messages=api_messages_history, 
                system=api_system_prompt
            )
            if response.content and len(response.content) > 0 and response.content[0].text:
                print("Réponse Claude reçue.")
                return response.content[0].text
            else:
                 print("Erreur: Réponse vide ou mal formée de l'API (obtenir_reponse).")
                 return "Désolé, j'ai reçu une réponse vide de l'IA Claude. Veuillez réessayer."
        except APIError as e:
            print(f"Erreur API Anthropic (obtenir_reponse): {type(e).__name__} ({e.status_code}) - {e.message}")
            return f"Désolé, une erreur API technique est survenue avec l'IA Claude ({e.status_code}). Veuillez réessayer."
        except Exception as e:
            print(f"API Error (Claude) in obtenir_reponse: {type(e).__name__} - {e}")
            return f"Désolé, une erreur technique est survenue avec l'IA Claude ({type(e).__name__}). Veuillez réessayer."

    def perform_web_search(self, query: str) -> str:
        """Effectue une recherche web via l'API Claude et retourne la synthèse des résultats."""
        if not query:
            return "Erreur: La requête de recherche est vide."
        
        print(f"[WEB] Recherche web pour: '{query}'")
        
        try:
            # Utiliser l'API Claude avec l'outil de recherche web
            response = self.anthropic.messages.create(
                model=self.model_name_global,
                max_tokens=4000,
                temperature=0.2, # Temperature can be lower for factual retrieval
                messages=[{"role": "user", "content": f"Recherche des informations sur : {query}"}], # Reformulated slightly for clarity
                tools=[{
                    "name": "web_search",  # CHAMP 'name' AJOUTÉ/CORRIGÉ
                    "type": "web_search_20250305"
                    # "description": "Performs a web search to find information relevant to the user's query.",
                    # "input_schema": {
                    #     "type": "object",
                    #     "properties": {"query": {"type": "string", "description": "The search query to perform."}},
                    #     "required": ["query"]
                    # }
                }]
            )
            
            result_text = ""
            # La documentation d'Anthropic (et l'usage commun des 'tools') suggère que la réponse
            # après un appel avec 'tools' peut soit contenir le résultat directement (si l'outil est "intégré"
            # et que Claude l'utilise en interne puis répond), soit un `stop_reason` de `tool_use`
            # indiquant que Claude attend que NOUS exécutions l'outil et lui fournissions le résultat.
            # L'outil `web_search_20250305` est censé être du premier type: Claude utilise la recherche
            # et incorpore les résultats dans sa réponse.

            if response.content and len(response.content) > 0:
                for content_block in response.content:
                    if content_block.type == 'text':
                        result_text += content_block.text + "\n"
                    # Il ne devrait normalement pas y avoir de bloc 'tool_use' pour *cet* outil spécifique,
                    # car Claude est censé l'exécuter lui-même et renvoyer le texte.
                    # Si un bloc 'tool_use' est présent pour 'web_search_20250305', c'est inattendu
                    # ou indique un flux plus complexe non décrit ici.
                
                result_text = result_text.strip()
                
                if result_text:
                    print(f"[WEB] Réponse obtenue, longueur: {len(result_text)} caractères")
                    return result_text
                elif response.stop_reason == "tool_use":
                     # Ceci est inattendu pour web_search_20250305 s'il est entièrement géré par Claude.
                     print(f"[WEB] Avertissement: stop_reason 'tool_use' reçu pour web_search. Contenu de la réponse: {response.content}")
                     return "Claude a indiqué qu'il utilisait la recherche, mais aucun résultat textuel n'a été fourni directement. Cela pourrait indiquer un problème ou un flux inattendu."
                else:
                    return "La recherche n'a pas produit de résultats textuels clairs."
            else:
                return "La recherche n'a pas produit de résultats. Essayez une requête différente."
                
        except APIError as e: # Être plus spécifique sur l'erreur API Anthropic
            error_message = f"Erreur API Anthropic lors de la recherche web ({e.status_code}): {e.message}"
            print(f"[WEB] {error_message}")
            # Imprimer le corps de l'erreur si disponible, peut aider au débogage
            if e.body:
                print(f"[WEB] Corps de l'erreur API: {e.body}")
            import traceback
            traceback.print_exc()
            return f"Erreur lors de la recherche web: {type(e).__name__} ({e.status_code}). Veuillez réessayer."
        except Exception as e:
            print(f"[WEB] Erreur générique lors de la recherche: {type(e).__name__} - {str(e)}")
            import traceback
            traceback.print_exc()
            return f"Erreur lors de la recherche web: {type(e).__name__}. Veuillez réessayer."

# --- FIN CLASSE ExpertAdvisor ---
